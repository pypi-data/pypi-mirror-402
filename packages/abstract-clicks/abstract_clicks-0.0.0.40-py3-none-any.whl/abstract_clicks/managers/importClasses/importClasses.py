
class getAutoGui:
    def __init__(self):
        
        self.py_auto_gui = None
    def import_auto_gui(self):
        import pyautogui
        return pyautogui
    def get_auto_gui(self):
        if self.py_auto_gui == None:
            self.py_auto_gui = self.import_auto_gui()
        return self.py_auto_gui
class getUserInput:
    def __init__(self):
        
        self.getUserInputwindow = None
    def user_input_window(self):
        from abstract_gui.QT5 import getUserInputwindow
        return getUserInputwindow
    def get_user_input_window(self):
        if self.getUserInputwindow == None:
            self.getUserInputwindow = self.user_input_window()
        return self.getUserInputwindow


def get_auto_gui():
    auto_gui_mgr = getAutoGui()
    return auto_gui_mgr.get_auto_gui()
def get_user_input():
    user_input_mgr = getUserInput()
    return user_input_mgr.get_user_input_window()
def get_user_input_window():
    getUserInputwindow = get_user_input()
    prompt="please enter the event type"
    title="event type"
    exitcall, event_type = getUserInputwindow(prompt=prompt,
                                              title=title)
    return exitcall, event_type

