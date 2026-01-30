from .shadow_main import *
def make_title(title=None, url=None, html_content=None, html_file_path=None):
    return titlemanager.make_title(title=title, url=url, html_content=html_content, html_file_path=html_file_path)

def get_title_from_url(url):
    return titlemanager.get_title_from_url(url=url)

def get_all_titles():
    return titlemanager.get_all_titles()
