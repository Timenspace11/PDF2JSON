import json

from trying.ocr import details_extraction
from trying.row import group_rows

def row_to_string(row):
    """
    Convert a row (list of OCR item dictionaries) into a single string 
    by joining the 'text' fields with commas.
    """
    return ", ".join(item["text"] for item in row)

def process_document_flow(rows_grouped, min_cells=2):
    """
    Process OCR rows in their sequential order and produce a list of blocks,
    preserving the natural flow of the PDF.
    
    Blocks are:
      - Text blocks: {"type": "text", "content": <string>}
      - Table blocks: a dictionary with a key "TABLE<i>" mapping to an array of row objects.
        Each table's first row is used as header, and the subsequent rows are mapped by header.
    
    If a row, split by commas, yields at least `min_cells` cells, it is considered a table candidate.
    """
    blocks = []
    active_table = []         # Accumulates candidate table rows (each row represented as a list of cells)
    expected_cell_count = None
    table_index = 0           # Counter for naming tables as TABLE1, TABLE2, etc.

    def flush_active_table():
        nonlocal active_table, expected_cell_count, table_index, blocks
        if active_table:
            if len(active_table) >= 2:  # Two or more rows form a table (header + at least one data row)
                header = [cell.strip() for cell in active_table[0]]
                table_rows = []
                for row_cells in active_table[1:]:
                    if len(row_cells) == len(header):
                        row_obj = { header[i]: row_cells[i].strip() for i in range(len(header)) }
                        table_rows.append(row_obj)
                    else:
                        # If row cell count mismatches header, skip it (or handle as needed)
                        continue
                table_index += 1
                blocks.append({ f"TABLE{table_index}": table_rows })
            else:
                # Single row; treat it as text.
                single_text = ", ".join(active_table[0])
                blocks.append({ "type": "text", "content": single_text })
        active_table.clear()
        expected_cell_count = None

    # Process each row in its original order.
    for row in rows_grouped:
        row_str = row_to_string(row)
        cells = [cell.strip() for cell in row_str.split(",")]
        
        if len(cells) >= min_cells:  
            # This row qualifies as a table candidate.
            if active_table:
                # Already in a table candidate group: verify cell count consistency.
                if len(cells) == expected_cell_count:
                    active_table.append(cells)
                else:
                    flush_active_table()
                    active_table.append(cells)
                    expected_cell_count = len(cells)
            else:
                # Starting a new table candidate group.
                active_table.append(cells)
                expected_cell_count = len(cells)
        else:
            # This row doesn't qualify as a table row; flush any active table first.
            if active_table:
                flush_active_table()
            blocks.append({ "type": "text", "content": row_str })
    
    # Flush any remaining candidate table.
    if active_table:
        flush_active_table()
    
    return blocks




# ---------------------------
# # Example usage:

# # Simulated OCR rows as produced by your row extraction logic:
# rows_grouped = [
#     # Row 1: a simple text (title)
#     [{'box': [[592.0, 402.0], [1168.0, 402.0], [1168.0, 450.0], [592.0, 450.0]], 
#       'text': 'UNIVERSITY OF OREGON', 'conf': 0.9869, 'y_center': 426.0, 'height': 48.0}],
#     # Row 2: another text row
#     [{'box': [[298.0, 577.0], [981.0, 577.0], [981.0, 636.0], [298.0, 636.0]], 
#       'text': 'PDF Accessibility - Tables', 'conf': 0.9496, 'y_center': 606.5, 'height': 59.0}],
#     # Row 3: description text
#     [{'box': [[298.0, 657.0], [1677.0, 657.0], [1677.0, 705.0], [298.0, 705.0]], 
#       'text': 'This is a sample document to demonstrate how to make accessible tables.', 
#       'conf': 0.9825, 'y_center': 681.0, 'height': 48.0}],
#     # Row 4: a heading
#     [{'box': [[298.0, 756.0], [579.0, 756.0], [579.0, 804.0], [298.0, 804.0]], 
#       'text': 'Simple Table', 'conf': 0.9994, 'y_center': 780.0, 'height': 48.0}],
#     # Row 5: table caption or description that appears as text
#     [{'box': [[300.0, 860.0], [900.0, 860.0], [900.0, 900.0], [300.0, 900.0]], 
#       'text': 'Sales figures by salesperson and year (in thousands)', 'conf': 0.99, 
#       'y_center': 880.0, 'height': 40.0}],
#     # Row 6: table header row (note the comma-separated values)
#     [{'box': [[300.0, 920.0], [600.0, 920.0], [600.0, 960.0], [300.0, 960.0]], 
#       'text': 'Susan,  Keisha, Year, Gerald, Bobbie, Art', 'conf': 0.98, 
#       'y_center': 940.0, 'height': 40.0}],
#     # Row 7: table data row
#     [{'box': [[300.0, 1000.0], [600.0, 1000.0], [600.0, 1040.0], [300.0, 1040.0]], 
#       'text': '570, 635, 684, 397, 678, 2017', 'conf': 0.97, 
#       'y_center': 1020.0, 'height': 40.0}],
# ]




img_path = r"C:\Users\Thakur\Desktop\PDF Extraction\images\page_1.png"
ocr_results = details_extraction(img_path)
# Group the OCR items into rows.
rows_grouped = group_rows(ocr_results[0], k=0.5)


document_flow = process_document_flow(rows_grouped)
final_json = {"document": document_flow}

print(json.dumps(final_json, indent=2))


# Example usage:
# Suppose rows_grouped is the list you have from your OCR row extraction.


# # First, extract table candidate groups from the rows.
# table_candidates = extract_table_candidates(rows_grouped, min_cells=2)

# # Now convert these candidate tables to a meaningful JSON structure.
# tables_json = convert_tables_to_json(table_candidates)

# print(json.dumps(tables_json, indent=2))
