from ..clipboardManager import ClipboardManager
def get_clipboard():
    clipboard = ClipboardManager()
    return clipboard
clipboard = get_clipboard()


def get_extracted_texts_and_coords(img,confidence_threshold=None,objectType=None):
    return clipboard.get_extracted_texts_and_coords(img=img,
                                                    confidence_threshold=confidence_threshold,
                                                    objectType=objectType)


def perform_ocr(screenshot_file="new_screen.png",
                confidence_threshold=60):
    return clipboard.perform_ocr(screenshot_file=screenshot_file,
                                 confidence_threshold=confidence_threshold)

def move_mouse_to_text(extracted_texts,monitor_info,
                       text_index=0,
                       target_text=None):
    return clipboard.move_mouse_to_text(extracted_texts=extracted_texts,
                                        monitor_info=monitor_info)





def get_ocr_locate_image(main_file_path=None,
                         template_file_path=None,
                         text=None):
    return clipboard.ocr_locate_image(main_file_path=main_file_path,
                                      template_file_path=template_file_path,
                                      text=text)

