from ..imports import *
def get_screenshot_file_path(screenshot):
    screenshot = screenshot or "new_screen.png"
    if os.path.isdir(screenshot):
        screenshot = os.path.join(screenshot,screenshot_default_basename)
    elif not os.path.isfile(screenshot):
        dirname = os.path.dirname(screenshot)
        if not os.path.isdir(dirname):
            screenshot = os.path.join(os.getcwd(),screenshot)
    return screenshot
def get_extracted_texts_and_coords(img, confidence_threshold=None):
    confidence_threshold = confidence_threshold or 60
    extracted_texts=[]
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > confidence_threshold:
            text = data['text'][i]
            if text.strip():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                #print(f"Text: '{text}', X: {x}, Y: {y}, Width: {w}, Height: {h}")
                extracted_texts.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'confidence': data['conf'][i]
                })
    return extracted_texts

