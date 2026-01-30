#from ..managers import get_auto_gui
def move_mouse_to_text(extracted_texts, monitor_info, text_index=0, target_text=None):
    """Move the mouse to the center of a text box from OCR results."""
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
                    selected_texts = [text for text in extracted_texts[text_index] if target_text.lower() in text['text_lower'].lower()]
                
            else:
                print(f"Invalid text index: {text_index}. Available texts: {len(extracted_texts)}")
                return False
        
        if not selected_text or selected_texts:
            print(f"Target text '{target_text}' not found.")
            return False
        selected_text = selected_text or selected_texts[0]
        # Calculate center of text box
        x = selected_text['x'] + selected_text['width'] // 2
        y = selected_text['y'] + selected_text['height'] // 2
        
        # Adjust for monitor offset
        if monitor_info:
            x += monitor_info['left']
            y += monitor_info['top']
        
        # Move mouse
        get_auto_gui().moveTo(x, y, duration=0.5)  # Smooth movement over 0.5s
        print(f"Moved mouse to text '{selected_text['text']}' at screen coordinates ({x}, {y})")
        return True
    except Exception as e:
        
        print(f"Error moving mouse: {e}")
        return False
