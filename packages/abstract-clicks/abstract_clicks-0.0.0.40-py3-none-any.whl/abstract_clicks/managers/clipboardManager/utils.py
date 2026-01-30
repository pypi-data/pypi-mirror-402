from ...imports import *
import pyautogui
def image_to_data(file_name,outputType=None):
    outputType = outputType or 'DICT'
    pytesseractOutput = getattr(pytesseract.Output,outputType)
    img = Image.open(file_name)
    data = pytesseract.image_to_data(img,output_type=pytesseractOutput)
    return data
def paste_modifier():
    modifier = 'command' if platform.system() == 'Darwin' else 'ctrl'
    pyautogui.hotkey(modifier,'v')
def custom_copy(text,
                clip=None):
    """Wrap pyperclip.copy to track program-initiated copies."""
    clip = clip or pyperclip
    clip.copy(text)
    print(f"Program copied: {text}")
def paste_to_file(file_path,
                  clip=None):
        clip = clip or pyperclip
        # Get clipboard content and save to file
        try:
            data = clip.paste()
            safe_dump_to_file(data=data,
                              file_path=file_path)
            print(f"Performed paste action and saved clipboard content to {file_path}")
        except Exception as e:
            print(f"Error saving clipboard content: {e}")
def perform_ocr(screenshot_file="new_screen.png",
                confidence_threshold=60):
    """Perform OCR on a screenshot and return extracted text with coordinates."""
    extracted_texts = []
    try:
        data = image_to_data(screenshot_file,outputType='DICT')
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
                    extracted_texts.append({'text': text,'x': x,'y': y,'width': w,'height': h,'confidence': data['conf'][i]})
        if extracted_texts:
            text_to_copy = "\n".join([item['text'] for item in extracted_texts])
            custom_copy(text_to_copy)
        return extracted_texts
    except FileNotFoundError:
        print("Error: The screenshot file was not found.")
        return []
    except Exception as e:
        print(f"Error during OCR: {e}")
        print("Ensure Tesseract is installed and configured correctly.")
        return []



def get_selected_text(extracted_texts=[],
                      text_index=None,
                      selected_text=None,
                      target_text=None):
    """Move the mouse to the center of a text box from OCR results."""
    selected_texts = []
    if not extracted_texts:
        print("No text found to move mouse to.")
        return False
    try:
        # Select text box
        selected_text = None
        if target_text:
            for item in extracted_texts:
                if target_text.lower() in item['text'].lower():
                    selected_text = item
                    break
        else:
            if text_index < len(extracted_texts):
                selected_text = extracted_texts[text_index]
                
                if not selected_text:
                    selected_texts = [text for text in extracted_texts[text_index] if target_text.lower() in text['text'].lower()]
                
            else:
                print(f"Invalid text index: {text_index}. Available texts: {len(extracted_texts)}")
                return False,False
        
        if not selected_text or selected_texts:
            print(f"Target text '{target_text}' not found.")
            return False,selected_texts
        selected_text = selected_text or selected_texts[0]
        return selected_text,selected_texts
    except FileNotFoundError:
        print("Error: The screenshot file was not found.")
        return False,False
    except Exception as e:
        print(f"Error during OCR: {e}")
        print("Ensure Tesseract is installed and configured correctly.")
        return False,False

def selected_text_pyautogui(selected_text=None,selected_texts=[]):
    selected_text = selected_text or selected_texts[0]
    # Calculate center of text box
    x = selected_text['x'] + selected_text['width'] // 2
    y = selected_text['y'] + selected_text['height'] // 2
    
    # Adjust for monitor offset
    if monitor_info:
        x += monitor_info['left']
        y += monitor_info['top']
    
    # Move mouse
    pyautogui.moveTo(x, y, duration=0.5)  # Smooth movement over 0.5s
    print(f"Moved mouse to text '{selected_text['text']}' at screen coordinates ({x}, {y})")
    return True
def move_mouse_to_text(extracted_texts,
                       monitor_info,
                       text_index=0,
                       target_text=None):
    """Move the mouse to the center of a text box from OCR results."""
    if not extracted_texts:
        print("No text found to move mouse to.")
        return False
    try:
        # Select text box
        selected_text,selected_texts = get_selected_text(extracted_texts=extracted_texts,
                      selected_text=selected_text,
                      target_text=target_text)
        
        if not selected_text or selected_texts or [selected_text,selected_texts] == [False,False]:
            if [selected_text,selected_texts] == [False,False]:
                print(f"Invalid text index: {text_index}. Available texts: {len(extracted_texts)}")
                return False
            print(f"Target text '{target_text}' not found.")
            return False
        return selected_text_pyautogui(selected_text=None,selected_texts=[])
    except Exception as e:
        
        print(f"Error moving mouse: {e}")
        return False


def switch_window(window_title="My Permanent Tab"):
    """Switch to a window by partial title match (Linux with xdotool)."""
    if platform.system() != 'Linux':
        modifier = 'command' if platform.system() == 'Darwin' else 'alt'
        try:
            pyautogui.keyDown(modifier)
            time.sleep(0.1)
            pyautogui.press('tab')
            time.sleep(0.1)
            pyautogui.keyUp(modifier)
            print("Switched to first window (non-Linux fallback)")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error switching window: {e}")
        return
    try:
        result = subprocess.run(
            ['xdotool', 'search', '--name', window_title],
            capture_output=True, text=True
        )
        window_ids = result.stdout.strip().split()
        if not window_ids:
            print(f"No window found with title containing: {window_title}")
            return
        subprocess.run(
            [
                'xdotool',
                'activate',
                window_ids[0]
                ]
            )
        print(f"Switched to window with title containing: {window_title}")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error switching window with xdotool: {e}")
