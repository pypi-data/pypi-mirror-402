import webbrowser
from PIL import Image
import pytesseract
import mss
import pyperclip
import time
import threading
import platform
import os
import subprocess
import time
import json
import math
import sys

from typing import (Any,
                    Dict,
                    List,
                    Optional,
                    Tuple
                    )
from abstract_utilities import (SingletonMeta,
                                safe_dump_to_file,
                                safe_load_from_file,
                                read_from_file
                                )
from abstract_utilities.class_utils import get_class_inputs as get_inputs
from abstract_utilities.compare_utils import get_closest_match_from_list
from abstract_webtools import get_soup
from pynput import mouse, keyboard
from random import uniform
import base64
import uuid
import pytesseract
import shutil

pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")
if not tesseract_cmd:
    raise RuntimeError("tesseract not found in PATH")


# get a UUID - URL safe, Base64
import uuid

def get_uuid_id():
    return str(uuid.uuid4())
# ——— Globals ———
def get_abs_file():
    return os.path.abspath(__file__)
def get_abs_dir():
    abs_file = get_abs_file()
    return os.path.dirname(abs_file)
def get_abs_path(path):
    abs_dir = get_abs_dir()
    return os.path.join(abs_dir,path)
def get_abs_parent_path(path):
    abs_dir = get_abs_dir()
    dirname = os.path.dirname(abs_dir)
    return os.path.join(dirname,path)
def get_rel_dir():
    rel_dir = os.getcwd()
    return rel_dir
def get_rel_path(path):
    rel_dir = get_abs_dir()
    return os.path.join(rel_dir,path)
def get_datas_dir():
    datas_folder  = get_abs_parent_path('datas')
    os.makedirs(datas_folder,exist_ok=True)
    return datas_folder
def get_sessions_dir():
    datas_dir = get_datas_dir()
    sessions_folder  = os.path.join(datas_dir,'sessions')
    os.makedirs(sessions_folder,exist_ok=True)
    return sessions_folder

def get_chat_dirs():
    datas_dir = get_datas_dir()
    chat_dirs  = os.path.join(datas_dir,'chatDirs')
    os.makedirs(chat_dirs,exist_ok=True)
    return chat_dirs

def get_queries_dir():
    chat_dirs = get_chat_dirs()
    queries_dir  = os.path.join(chat_dirs,'queries')
    os.makedirs(queries_dir,exist_ok=True)
    return queries_dir

def get_prompts_dir():
    chat_dirs = get_chat_dirs()
    prompts_dir = os.path.join(chat_dirs,'prompts')
    os.makedirs(prompts_dir,exist_ok=True)
    return prompts_dir

def get_responses_dir():
    chat_dirs = get_chat_dirs()
    responses_dir = os.path.join(chat_dirs,'responses')
    os.makedirs(responses_dir,exist_ok=True)
    return responses_dir

def get_queried_dir():
    chat_dirs = get_chat_dirs()
    queried_dir = os.path.join(chat_dirs,'queried')
    os.makedirs(queried_dir,exist_ok=True)
    return queried_dir

def get_response_path(path=None):
    path = path or 'new_response.txt'
    responses_dir = get_responses_dir()
    response_file_path = os.path.join(responses_dir,path)
    return response_file_path

def get_query_path(path=None):
    path = path or 'new_query.txt'
    queries_dir = get_queries_dir()
    query_file_path = os.path.join(queries_dir,path)
    return query_file_path

def get_prompt_path(path=None):
    path = path or 'new_prompt.txt'
    prompts_dir = get_prompts_dir()
    prompt_file_path = os.path.join(prompts_dir,path)
    return prompt_file_path

def get_events_path(path,default=None):
    path = path or default or "session.json"
    if os.path.exists(path):
        return path
    dirname = os.path.dirname(path)
    if dirname and os.path.isdir(dirname):
        return path
    return get_rel_path(path)

def get_time():
    return time.time()

def get_time_span(start_time):
    time_span = get_time() - start_time
    return time_span

def resolve_events_path(path, default=None):
    path = path or default or get_rel_path("session.json")
    dirname = os.path.dirname(path)
    if os.path.exists(path):
        return path
    dirname = os.path.dirname(path)
    if dirname and os.path.isdir(dirname):
        return path
    return get_rel_path(path)


def get_default_session_path():
    sessions_dir = get_sessions_dir()
    uuid = get_uuid_id()
    default_session_path = os.path.join(sessions_dir,f'{uuid}_default.json')
    return default_session_path
# Time utilities
def now() -> float:
    return time.time()

def elapsed(start: float) -> float:
    return now() - start
def call_soup(url=None, soup=None):
    """Retrieve BeautifulSoup object for a URL or return existing soup."""
    if url and not soup:
        soup = get_soup(url)
    return soup

def get_title(url=None, soup=None):
    """Extract the title from a URL or BeautifulSoup object."""
    try:
        soup = call_soup(url=url, soup=soup)
        if not soup:
            return ""
        title_tag = soup.find("title")
        if not title_tag:
            return ""
        title = str(title_tag).split('>')[1].split('<')[0]
        return title.strip()
    except Exception as e:
        print(f"Error getting title: {e}")
        return ""
