from abstract_flask import *
from abstract_clicks.imports import *
def get_abs_path():
    return os.path.abspath(__file__)
def get_abs_dir():
    abs_path = get_abs_path()
    dirname = os.path.dirname(abs_path)
    return dirname
def get_parent_dir():
    abs_dir = get_abs_dir()
    dirname = os.path.dirname(abs_dir)
    return dirname
def get_static_folder():
    parent_dir = get_parent_dir()
    static_folder = os.path.join(parent_dir,'static')
    os.makedirs(static_folder,exist_ok=True)
    return static_folder
def create_static_path(path):
    static_folder = get_static_folder()
    static_path = os.path.join(static_folder,path)
    os.makedirs(static_path,exist_ok=True)
    return static_path

URL_PREFIX = ""
STATIC_FOLDER = get_datas_dir()
RESPONSE_DIR = get_responses_dir()
QUERY_DIR = get_queries_dir()
RESPONSE_FILE_PATH = get_response_path()
QUERY_FILE_PATH = get_query_path()
