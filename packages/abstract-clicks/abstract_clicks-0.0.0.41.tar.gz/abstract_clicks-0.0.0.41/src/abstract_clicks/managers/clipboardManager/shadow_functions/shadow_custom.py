from .shadow_main import *


def response_custom_copy(text):
    return clipboard.custom_copy(text=text)

def response_custom_paste(file_path=None):
    file_path = file_path or get_prompt_path()
    return clipboard.custom_paste(file_path=file_path)

def query_custom_copy(text):
    return clipboard.custom_copy(text=text)

def query_custom_paste(file_path=None):
    return clipboard.custom_paste(file_path=file_path)
