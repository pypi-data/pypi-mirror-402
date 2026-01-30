
from .imports import *
from .utils import *



# Global state
clip_mgr = ClipboardManager()
clip_mgr.start_monitoring()
index = 0
ctrl_held = False

def on_press(key):
    global index, ctrl_held
    try:
        if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            ctrl_held = True
        elif key.char == 'v' and ctrl_held:
            # Prepare next cred BEFORE system paste consumes it
            cred = login_creds[index % len(login_creds)]
            clip_mgr.custom_copy(cred)
            print(f"Ctrl+V detected → preloaded: {cred}")
            index += 1
            # Now let OS paste it naturally
    except AttributeError:
        pass

def on_release(key):
    global ctrl_held
    if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
        ctrl_held = False

with keyboard.Listener() as listener:
    listener.join()
