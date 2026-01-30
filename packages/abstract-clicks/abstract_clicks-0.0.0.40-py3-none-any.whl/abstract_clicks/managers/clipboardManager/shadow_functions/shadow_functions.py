from .clipboardManager import ClipboardManager
def get_clipboard():
    clipboard = ClipboardManager()
    return clipboard
clipboard = get_clipboard()

def custom_copy(text):
    return clipboard.custom_copy(text=text)


def prompt_custom_copy(text):
    return clipboard.custom_copy(text=text)

def prompt_custom_paste(file_path=None):
    return clipboard.custom_paste(file_path=file_path)

def query_custom_copy(text):
    return clipboard.custom_copy(text=text)

def query_custom_paste(file_path=None):
    return clipboard.custom_paste(file_path=file_path)

def custom_paste(file_path=None):
    return clipboard.custom_paste(file_path=file_path)

def screenshot_specific_screen(output_file="new_screen.png",monitor_index=1):
    return clipboard.screenshot_specific_screen(output_file=output_file,
                                                monitor_index=monitor_index)

def switch_window(window_title="My Permanent Tab"):
    return clipboard.switch_window(window_title=window_title)

def get_open_browser_tab(url=None,title="My Permanent Tab"):
    return clipboard.get_open_browser_tab(url=url,
                                          title=title)

def get_extracted_texts_and_coords(img,confidence_threshold=None,objectType=None):
    return clipboard.get_extracted_texts_and_coords(img=img,
                                                    confidence_threshold=confidence_threshold,
                                                    objectType=objectType)

def monitor_clipboard(interval=0.5):
    return clipboard.monitor_clipboard(interval=interval)

def start_monitoring():
    return clipboard.start_monitoring()

def stop_monitoring():
    return clipboard.stop_monitoring()

def perform_ocr(screenshot_file="new_screen.png",
                confidence_threshold=60):
    return clipboard.perform_ocr(screenshot_file=screenshot_file,
                                 confidence_threshold=confidence_threshold)

def move_mouse_to_text(extracted_texts,monitor_info,
                       text_index=0,
                       target_text=None):
    return clipboard.move_mouse_to_text(extracted_texts=extracted_texts,
                                        monitor_info=monitor_info)

def get_open_browser_tab(url=None,title="My Permanent Tab"):
    return clipboard.open_browser_tab(url=url,
                                          title=title)
def get_ocr_locate_image(main_file_path=None,
                         template_file_path=None,
                         text=None):
    return clipboard.ocr_locate_image(main_file_path=main_file_path,
                                      template_file_path=template_file_path,
                                      text=text)

def screenshot_specific_screen(output_file="new_screen.png",monitor_index=1):
    return clipboard.screenshot_specific_screen(output_file=output_file,
                                                monitor_index=monitor_index)

def switch_window(window_title="My Permanent Tab"):
    return clipboard.switch_window(window_title=window_title)


