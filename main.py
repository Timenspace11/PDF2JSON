import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
import numpy as np
import uvicorn
import os
import shutil
import json
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
from paddleocr import PaddleOCR
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI and PaddleOCR




app = FastAPI()

# Allow specific origins (for example, your React app)
origins = [
    "http://localhost:3000",
    "http://192.168.71.241:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ocr = PaddleOCR()

# ------------------------
# OCR & Document Processing Functions
# ------------------------

def details_extraction(image_input):
    """
    Run PaddleOCR on the input.
    If image_input is a string (file path), process from disk; otherwise, assume it is a PIL Image.
    """
    if isinstance(image_input, str):
        result = ocr.ocr(image_input, cls=True)
    else:
        # (This branch is now less frequently used since we are passing file paths.)
        result = ocr.ocr(image_input, cls=True)
    # print(result)    
    return result


# def row_to_string(row: list) -> str:
#     """
#     Convert a row (list of OCR item dictionaries) to a single string
#     by joining the 'text' values with commas.
#     """
#     return ", ".join(item["text"] for item in row)
def row_to_string(row: list) -> str:
    texts = []
    print("inside the function ", row)
    for item in row:
        # If the item is a bounding box (list of 4 numeric entries), skip it.
        if isinstance(item, list) and len(item) == 4 and all(isinstance(x, (int, float)) or (isinstance(x, list) and all(isinstance(z, (int, float)) for z in x)) for x in item):
            print("Skipping bounding box:", item)
            continue
        # If the item is a tuple, assume it's (text, confidence)
        elif isinstance(item, tuple):
            print("maybe")
            if len(item) > 0:
                texts.append(str(item[0]))
            else:
                texts.append("")
        # Fallback for dictionaries or other formats.
        elif isinstance(item, dict) and "text" in item:
            print("its a dict")
            texts.append(item["text"])
        else:
            print("gon on")
            texts.append(str(item))
    print("reaching the end")
    return ", ".join(texts)



def process_document_flow(rows_grouped: list, min_cells: int = 2) -> list:
    """
    Process OCR rows in their sequential order and create a document flow.
    Blocks are:
        - Text blocks: { "type": "text", "content": <string> }
        - Table blocks: { "TABLE<i>": [ row_object, row_object, ... ] }
    """
    blocks = []
    active_table = []  # Stores candidate table rows (each as a list of cell strings)
    expected_cell_count = None
    table_index = 0   # Counter used to name tables
    print("inside themain")
    def flush_active_table():
        nonlocal active_table, expected_cell_count, table_index, blocks
        print("reaching here")
        if active_table:
            print("inside if")
            if len(active_table) >= 2:  # Table candidate: header + at least 1 row
                header = [cell.strip() for cell in active_table[0]]
                table_rows = []
                for row_cells in active_table[1:]:
                    if len(row_cells) == len(header):
                        row_obj = { header[i]: row_cells[i].strip() for i in range(len(header)) }
                        table_rows.append(row_obj)
                table_index += 1
                blocks.append({ f"TABLE{table_index}": table_rows })
            else:
                # If only one row is present, treat it as a text block.
                single_text = ", ".join(active_table[0])
                blocks.append({ "type": "text", "content": single_text })
            print("this block is working")    
        active_table.clear()
        expected_cell_count = None
        print("expexted cell count")
    for row in rows_grouped:
        print("correct_path")
        row_str = row_to_string(row)
        print("row_str")
        cells = [cell.strip() for cell in row_str.split(",")]
        
        if len(cells) >= min_cells:
            # Candidate table row.
            print("inside cells")
            if active_table:
                if len(cells) == expected_cell_count:
                    active_table.append(cells)
                else:
                    flush_active_table()
                    active_table.append(cells)
                    expected_cell_count = len(cells)
            else:
                active_table.append(cells)
                expected_cell_count = len(cells)
        else:
            # Non-table row: flush any active table first.
            if active_table:
                flush_active_table()
            blocks.append({ "type": "text", "content": row_str })
    
    # Flush any remaining active table.
    if active_table:
        flush_active_table()
    print("near returning")
    return blocks

def get_y_center(box):
    # Compute the vertical center of a bounding box.
    ys = [point[1] for point in box]
    return (min(ys) + max(ys)) / 2

def get_height(box):
    # Compute the height of a bounding box.
    ys = [point[1] for point in box]
    return max(ys) - min(ys)

def group_rows(ocr_results, k=0.5):
    """
    Groups OCR results into rows.

    Parameters:
      ocr_results: List of OCR items. Each item is in the format:
                   [bounding_box, (text, confidence)]
      k: Factor to scale the calculated average height for the threshold.

    Returns:
      A list of rows where each row is a list of OCR items that are within the vertical threshold.
    """
    # Compute representative Y center and height for each OCR item.
    items = []
    for box, (text, conf) in ocr_results:
        y_center = get_y_center(box)
        height = get_height(box)
        items.append({
            'box': box,
            'text': text,
            'conf': conf,
            'y_center': y_center,
            'height': height
        })

    # Sort items by their y_center.
    items.sort(key=lambda x: x['y_center'])

    # Compute the average height to determine our dynamic threshold.
    avg_height = sum(item['height'] for item in items) / len(items)
    threshold = k * avg_height  # Adjust 'k' as needed based on testing.

    # Group items into rows based on the difference in y_center values.
    rows = []
    current_row = [items[0]]
    for prev, curr in zip(items, items[1:]):
        if abs(curr['y_center'] - prev['y_center']) < threshold:
            current_row.append(curr)
        else:
            rows.append(current_row)
            current_row = [curr]
    rows.append(current_row)  # Append the final row

    return rows


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list:
    """
    Convert the PDF at pdf_path into a list of images (one per page) as PNG byte streams.
    """
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.pil_tobytes(format="PNG"))
     
    return images

# ------------------------
# FastAPI Endpoint
# ------------------------

@app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     """
#     Upload an image or PDF file. If a PDF is uploaded, each page is converted to an image.
#     The file is processed via PaddleOCR, then converted into a JSON structure that preserves
#     the document flow (text blocks and table blocks inline).
#     """
#     # Allow common image formats and PDF.
#     if not (file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".pdf"))):
#         raise HTTPException(status_code=400, detail="Unsupported file type. Upload a JPG, PNG, or PDF.")

#     # Save the uploaded file temporarily.
#     os.makedirs("temp", exist_ok=True)
#     file_path = os.path.join("temp", file.filename)
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
    
#     try:
#         if file.filename.lower().endswith(".pdf"):
#             # Convert PDF to images.
#             images_bytes_list = pdf_to_images(file_path)
#             document_flow_all = []
#             for img_bytes in images_bytes_list:
#                 pil_image = Image.open(BytesIO(img_bytes))
#                 ocr_result = details_extraction(pil_image)
#                 print("Reached here")
#                 rows_grouped = group_rows(ocr_result)
#                 print("rows")
#                 page_flow = process_document_flow(rows_grouped)
#                 print("page_flow")
#                 document_flow_all.extend(page_flow)
#             final_output = {"document": document_flow_all}
#             print("final output")
#         else:
#             # Process image.
#             ocr_result = details_extraction(file_path)
#             rows_grouped = group_rows(ocr_result)
#             document_flow = process_document_flow(rows_grouped)
#             final_output = {"document": document_flow}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         # Clean up the temporary file.
#         os.remove(file_path)
    
#     return final_output

async def upload_file(file: UploadFile = File(...)):
    # Allow JPG, JPEG, PNG, and PDF.
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    # Save uploaded file temporarily.
    os.makedirs("temp", exist_ok=True)
    file_path = os.path.join("temp", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if file.filename.lower().endswith(".pdf"):
            # Convert PDF to images.
            images_bytes_list = pdf_to_images(file_path)
            document_flow_all = []
            for img_bytes in images_bytes_list:
                # Instead of immediately converting to a PIL image,
                # temporarily save the bytes as a PNG file and pass its path.
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(img_bytes)
                    temp_image_path = tmp.name

                # Now pass the file path to the OCR function.
                ocr_result = details_extraction(temp_image_path)
                print("Reached after OCR on file path")
                rows_grouped = group_rows(ocr_result[0]) # check this part for multipage pdf:
                print("rows processed")
                page_flow = process_document_flow(rows_grouped)
                print("page_flow processed")
                document_flow_all.extend(page_flow)
                
                # Remove the temporary image file
                os.remove(temp_image_path)
            final_output = {"document": document_flow_all}
        else:
            # For non-PDF files, we process as before using the file path.
            ocr_result = details_extraction(file_path)
            rows_grouped = group_rows(ocr_result)
            document_flow = process_document_flow(rows_grouped)
            final_output = {"document": document_flow}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the uploaded file
        os.remove(file_path)

    return final_output



# ------------------------
# Run the server
# ------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
