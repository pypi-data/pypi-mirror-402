from ..imports import *
import cv2
import matplotlib.pyplot as plt

def highlight_all_extracted_texts(
    screenshot_path: str,
    confidence_threshold: int = 60,
    highlight_color: tuple = (0, 255, 0),
    thickness: int = 2,
    output_path: str = None
):
    """
    1. Read the image from disk.
    2. Extract all text boxes above the confidence threshold.
    3. Draw a rectangle for each box.
    4. Display (via matplotlib) and optionally save.
    """
    # 1) load
    img = cv2.imread(screenshot_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image at {screenshot_path}")

    # 2) extract all boxes
    extracted = get_extracted_texts_and_coords(img, confidence_threshold)

    # 3) draw each rectangle
    for item in extracted:
        x, y, w, h = item['x'], item['y'], item['width'], item['height']
        cv2.rectangle(img, (x, y), (x + w, y + h), highlight_color, thickness)

    # 4) show via matplotlib
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(12, 8))
    plt.imshow(img_rgb)
    plt.axis('off')
    plt.title(f"All text ≥ {confidence_threshold}% highlighted")
    plt.show()

    # 5) optionally save
    if output_path:
        cv2.imwrite(output_path, img)
        print(f"Saved highlighted image to {output_path}")
def get_monitors():
    """
    Returns a list of monitor‐info dicts, one per screen.
    Each dict has keys 'left','top','width','height'.
    """
    with mss.mss() as sct:
        return sct.monitors[1:]

def get_monitor_info(index=1):
    """
    Returns the x/y/width/height of a single monitor.
    Index defaults to 1 (the primary display).
    """
    monitors = get_monitors()
    try:
        return monitors[int(index) - 1]
    except IndexError:
        raise ValueError(f"Monitor index {index} out of range; only {len(monitors)} available")
def highlight_text_boxes(img_path, boxes, color=(0,255,0), thickness=2, save_as=None):
    img = cv2.imread(img_path)
    for b in boxes:
        x,y,w,h = b['x'],b['y'],b['width'],b['height']
        cv2.rectangle(img,(x,y),(x+w,y+h), color, thickness)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.imshow(rgb); plt.axis('off'); plt.show()
    if save_as:
        cv2.imwrite(save_as, img)
def capture_monitor(monitor_index, output_path=None):
    monitors = get_monitors()
    try:
        m = monitors[monitor_index - 1]
    except IndexError:
        raise ValueError(f"Only {len(monitors)} monitors; asked for {monitor_index}")
    with mss.mss() as sct:
        img = sct.grab(m)
        pil_img = Image.frombytes("RGB", img.size, img.rgb)
        out = output_path or f"screen_{monitor_index}.png"
        pil_img.save(out)
        return out
def screenshot_specific_screen(output_file=None,monitor_index=None):
    """Capture a screenshot of a specific monitor."""
    try:
       
        monitor = get_monitor(monitor_index)
        sct_img = sct.grab(
            monitor
            )
        
        img = Image.frombytes(
            "RGB",
            sct_img.size,
            sct_img.rgb
            )
        output_file = output_file or os.path.join(
            os.getcwd(),
            f'screen_{monitor_index}.png'
            )
        
        img.save(
            output_file
            )
        print(
            f"Saved screenshot of monitor {monitor_index} to: {output_file}"
            )
        return output_file
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

def highlight_text_on_screenshot(screenshot_path=None,
                                 bbox=None,
                                 highlight_color=(
                                     0,
                                     255,
                                     0
                                     ),
                                 thickness=2,
                                 output_path=None
                                 ):
    """
    Displays a screenshot with a highlighted rectangle around the target text.

    :param screenshot_path: Path to the screenshot image file.
    :param bbox: A dict containing 'x', 'y', 'width', 'height' keys for the text bounding box.
    :param highlight_color: Tuple for the rectangle color in BGR (default green).
    :param thickness: Line thickness of the rectangle.
    :param output_path: If provided, saves the highlighted image to this path.
    """
    # Load image
    if not os.path.isfile(screenshot_path):
        screenshot_specific_screen(output_file=screenshot_path)
    img = cv2.imread(screenshot_path)
    dirname = os.path.dirname(screenshot_path)
    basename = os.path.basename(screenshot_path)
    filename,ext = os.path.splitext(basename)
    output_path = os.path.join(dirname,f"{filename}_highlight{ext}")

    if img is None:
        raise FileNotFoundError(f"Could not load image at {screenshot_path}")
    bbox = highlight_all_extracted_texts(
               screenshot_path=screenshot_path,
               confidence_threshold=60,
               output_path=output_path
           )

    # Coordinates for rectangle
    x, y = bbox['x'], bbox['y']
    w, h = bbox['width'], bbox['height']
    start_point = (x, y)
    end_point = (x + w, y + h)

    # Draw rectangle
    cv2.rectangle(img, start_point, end_point, highlight_color, thickness)

    # Convert BGR to RGB for matplotlib
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Display with matplotlib
    plt.figure(figsize=(8, 6))
    plt.imshow(img_rgb)
    plt.axis('off')
    plt.title('Highlighted Text')
    plt.show()

    # Optionally save
    if output_path:
        cv2.imwrite(output_path, img)

def get_monitor_texts_with_highlight(comp,screenshot_file,monitor_index=None):
    monitor_index = monitor_index or 1
    monitor_info = clipboard.screenshot_specific_screen(screenshot_file,
                                                        monitor_index)
    if monitor_info:
        dicts = clipboard.perform_ocr(screenshot_file=screenshot_file, confidence_threshold=60)
        texts = [text.get('text') for text in dicts]
        closest_match = get_closest_match_from_list(comp_obj=comp, total_list=texts, case_sensative=False)
        best_dicts = [item for item in dicts if item.get('text') == closest_match]
        if best_dicts:
            best = best_dicts[0]
            # Adjust for monitor offset
            best['x'] += monitor_info['left']
            best['y'] += monitor_info['top']
            # Highlight instead of moving mouse
            highlight_text_on_screenshot(screenshot_file, best)
            return True
    return False
def get_all_monitor_texts_with_highlight(comp,screenshot_file):
    monitors = get_monitors()
    for monitor_index,monitor in enumerate(monitors):
        if monitor_index < 1 or monitor_index >= len(monitors):
            print(f"Invalid monitor index: {monitor_index}. Available monitors: {len(monitors)-1}")
            continue
        get_monitor_texts_with_highlight(comp,screenshot_file,monitor_index)
