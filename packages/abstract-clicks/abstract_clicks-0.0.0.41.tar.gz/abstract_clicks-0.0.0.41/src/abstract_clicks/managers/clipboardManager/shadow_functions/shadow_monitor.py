from .shadow_main import *

def monitor_clipboard(interval=0.5):
    return clipboard.monitor_clipboard(interval=interval)

def start_monitoring():
    return clipboard.start_monitoring()

def stop_monitoring():
    return clipboard.stop_monitoring()
