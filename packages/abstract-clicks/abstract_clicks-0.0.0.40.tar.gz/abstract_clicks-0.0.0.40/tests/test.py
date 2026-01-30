
from windowManager import *
from monitors import *
import subprocess, time, platform
import pyautogui
# ------------------------------------------------------------
# CLI test
# ------------------------------------------------------------




for e in resolve_ui_state():
    input(e)
    mon = get_monitor_for_pid(e.pid)
    print(f"PID {e.pid} → monitor:", mon)
    input(e.geometry)
    if mon["confidence"].startswith("high"):
        move_entity_to_monitor(entity=e)
    else:
        print("⚠️  Not moving: insufficient authority")
