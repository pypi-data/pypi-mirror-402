from watchdog.events import FileSystemEventHandler
class ChangeHandler(FileSystemEventHandler):
    def __init__(self, target_path, callback):
        super().__init__()
        self.target_path = target_path
        self.callback = callback

    def on_modified(self, event):
        if event.src_path == self.target_path:
            print(f"Detected change in {event.src_path}")
            self.callback(event.src_path)
