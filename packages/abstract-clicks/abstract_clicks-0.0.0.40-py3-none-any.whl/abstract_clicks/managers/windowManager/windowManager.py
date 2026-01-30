from .window_functions import *
class WindowManager(metaclass=SingletonMeta):
    def __init__(self,html_file_path=None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.html_file_path=html_file_path
    def open_browser_tab(self,*args,**kwargs):
        return self.open_browser_tab(*args,**kwargs)
    def get_existing_browser_info(self,*args,**kwargs):
        return self.get_existing_browser_info(*args,**kwargs)
    def screenshot_specific_screen(self,*args,**kwargs):
        return self.screenshot_specific_screen(*args,**kwargs)
    def get_window_monitor(self,*args,**kwargs):
        return self.get_window_monitor(*args,**kwargs)
    def switch_window(self,*args,**kwargs):
        return self.switch_window(window_title=window_title)
def get_window_mgr():
    window_mgr = WindowManager()
    return window_mgr

