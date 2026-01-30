from ..imports import *
from ..managers import *
from ..managers.titleManager.browser_functions import *
def click_conversations(extracted_texts,
                        monitor_info):
    keys = [
        ["indexeddb","index","ed","db"],
        ["https://chatgpt.com","https://","chatgpt",".com"],
        ["conversationsDatabase (default)","convers","ations","Data","base"," (default)"],
        ["conversations","convers","ations"],
        ["color","-","sche","me",":"," ","dark",";"],
    ]
    for key_parts in keys:
        for key in key_parts:
            outcome = clipboard.move_mouse_to_text(
                extracted_texts,
                monitor_info,
                target_text=key
                )
            if outcome:
                break
def get_monitor_texts(comp):
    screenshot_file = "new_screen.png"
    for monitor_index in range(3):	  # Change to 2, 3, etc., for other monitors
        monitor_info = clipboard.screenshot_specific_screen(screenshot_file,
                                                            monitor_index)
        if monitor_info:
            dicts = clipboard.perform_ocr(screenshot_file=file_path,
                                          confidence_threshold=60)#clipboard.perform_ocr(file_path)
            texts = [text.get('text') for text in dicts]
            closest_match = get_closest_match_from_list(comp_obj=comp,
                                                        total_list=texts,case_sensative=False)
            best_dict = [item for item in dicts if item.get('text') == closest_match]
            if best_dict:
                best_dict = best_dict[0]
                x = best_dict['x'] + best_dict['width'] // 2
                y = best_dict['y'] + best_dict['height'] // 2
                # Adjust for monitor offset
                if monitor_info:
                    x += monitor_info['left']
                    y += monitor_info['top']
                # Move mouse
                pyautogui.moveTo(x, y, duration=0.5)  # Smooth movement over 0.5s
                return True
def get_monitor_text(target_text):
    # Capture screenshot of specific monitor
    get_monitor_texts()
            
    # Move mouse to first text (or specify target_text="some text")
    if extracted_texts:
        #clipboard.move_mouse_to_text(extracted_texts, monitor_info, text_index=0)
        # Example with specific text:
        result = clipboard.move_mouse_to_text(extracted_texts, monitor_info, target_text=target_text)
        if result:
            return True

def get_gpt_browser():
    browser_js = get_browser_tab_and_index(url='https://chatgpt.com',
                          title="chatgpt")
    return browser_js
##info = get_open_browser_tab(url='https://chatgpt.com',title="chatgpt")
def get_confidence(string,comp):
    found = ['']
    comp = comp.lower()
    string = string.lower()
    string_len = len(string)
   
    for i in range(string_len):
        if string_len>i:
            nustring = string[:i+1]
            nu_len = len(list(nustring))
            if nustring in comp:
                found.append(nustring)
    items = [len(item) for item in found] or [0]
    items.sort()
    if items[0] >0:
        return items[0]/strinresultg_len
    return 0
def get_html_inspect(result):
    # Capture screenshot of specific monitor
    if result:
        pyautogui = get_auto_gui()
        pyautogui.click(clicks=1)
        pyautogui.click(button='right')
        pyautogui.press('esc')
        pyautogui.press('f2')
        pyautogui.hotkey('ctrl', 'i')
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.hotkey('ctrl', 'c')
        # Switch to a window
        print("Switching to window in 3 seconds...")
        # Paste extracted text
        print("Pasting extracted text in 1 second...")
        time.sleep(3)
        clipboard.custom_paste()
        return True
def get_paste_in_prompt(result):
    # Capture screenshot of specific monitor
    if result:
        pyautogui = get_auto_gui()
        pyautogui.click(clicks=1)
        pyautogui.click(button='right')
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.hotkey('Enter')
        # Switch to a window
        print("Switching to window in 3 seconds...")
        # Paste extracted text
        print("Pasting extracted text in 1 second...")
        
        clipboard.custom_paste()
        return True
def get_paste_in_prompt(result):
    
    # Capture screenshot of specific monitor
    if result:
        pyautogui = get_auto_gui()
        pyautogui.click(clicks=1)
        pyautogui.click(button='right')
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.hotkey('Enter')
        # Switch to a window
        print("Switching to window in 3 seconds...")
        # Paste extracted text
        print("Pasting extracted text in 1 second...")
        
        clipboard.custom_paste()
        return True
def open_inspect():
 
    randomize_pointer_in_browser_area(info.get('window_id'), area_offsets=None,
                                      half='right')
    pyautogui.click(button='right')
    pyautogui.hotkey('ctrl',
                     'shift',
                     'q')
