# import pytesseract
# from PIL import Image
# import io

# def extract_ocr_data(image_bytes):
#     image = Image.open(io.BytesIO(image_bytes))
#     ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
#     results = []
#     n_boxes = len(ocr_data['text'])
#     for i in range(n_boxes):
#         if ocr_data['text'][i].strip():
#             left = ocr_data['left'][i]
#             top = ocr_data['top'][i]
#             width = ocr_data['width'][i]
#             height = ocr_data['height'][i]
#             text = ocr_data['text'][i]
#             results.append({
#                 'text': text,
#                 'left': left,
#                 'top': top,
#                 'right': left + width,
#                 'bottom': top + height
#             })
#     return results



from paddleocr import PaddleOCR

# Initialize PaddleOCR
ocr = PaddleOCR()

# Run OCR on an image
def details_extraction(image_path):
    result = ocr.ocr(image_path, cls=True)
    
    return result
