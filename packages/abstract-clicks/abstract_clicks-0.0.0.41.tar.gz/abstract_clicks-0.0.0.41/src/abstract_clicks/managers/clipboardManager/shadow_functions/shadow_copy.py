from .shadow_main import *
def custom_paste(file_path=None):
    return clipboard.custom_paste(file_path=file_path)

def custom_copy(text):
    return clipboard.custom_copy(text=text)
