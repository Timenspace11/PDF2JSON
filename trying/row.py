from trying.ocr import details_extraction


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



img_path = r"C:\Users\Thakur\Desktop\PDF Extraction\images\page_1.png"
ocr_results = details_extraction(img_path)
# Group the OCR items into rows.
rows_grouped = group_rows(ocr_results[0], k=0.5)   # we have to think of the case as here only it is for one page  :  ocr_results[0]
print(type(rows_grouped))
print(rows_grouped)


# Now for deciding the 
# Display the results.
# for idx, row in enumerate(rows_grouped, start=1):
#     texts = ", ".join(item['text'] for item in row)
#     print(f"Row {idx}: {texts}")
