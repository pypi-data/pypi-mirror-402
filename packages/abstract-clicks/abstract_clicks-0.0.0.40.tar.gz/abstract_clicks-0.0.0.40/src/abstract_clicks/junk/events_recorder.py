import os
import time
import json
from typing import Any, Dict, List, Optional, Tuple
from abstract_utilities import SingletonMeta, os, safe_dump_to_file, safe_load_from_file
from pynput import mouse, keyboard
import time, json, sys, os

# Lazy-loaded modules
auto_gui: Any = None
_user_input_window: Any = None




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
        from abstract_gui import getUserInputwindow
        return getUserInputwindow
    def get_user_input_window(self):
        if self.getUserInputwindow == None:
            self.getUserInputwindow = self.user_input_window()
        return self.getUserInputwindow


def get_auto_gui():
    auto_gui_mgr = getAutoGui()
    return auto_gui_mgr.py_auto_gui
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



# Path utilities
def abs_path(path: str) -> str:
    return os.path.abspath(path)


def abs_dir(path: str = __file__) -> str:
    return os.path.dirname(abs_path(path))


def rel_path(path: str) -> str:
    return os.path.join(os.getcwd(), path)


def resolve_events_path(
    path: Optional[str],
    default: str = "session.json"
) -> str:
    p = path or default
    if os.path.exists(p):
        return p
    dirname = os.path.dirname(p)
    if dirname and os.path.isdir(dirname):
        return p
    return rel_path(p)


# Time utilities
def now() -> float:
    return time.time()


def elapsed(start: float) -> float:
    return now() - start


class EventsRecorder(metaclass=SingletonMeta):
    """
    Singleton for recording and replaying mouse/keyboard events.
    """

    def __init__(
        self,
        events_path: Optional[str] = None,
        start_time: Optional[float] = None,
        refresh: bool = False
    ):
        if refresh:
            self.initialized = False

        if not getattr(self, 'initialized', False):
            self.initialized = True
            self.events_path = resolve_events_path(events_path)
            self.start_time = start_time or now()
            self.events: List[Dict[str, Any]] = []
            self.all_events: Dict[str, List[Dict[str, Any]]] = {}
            self.mouse_listener: Optional[mouse.Listener] = None
            self.keyboard_listener: Optional[keyboard.Listener] = None

    def record_event(self, evt_type: str, **data) -> None:
        self.events.append({
            "time": elapsed(self.start_time),
            "type": evt_type,
            **data
        })

    # Mouse callbacks
    def on_move(self, x: int, y: int) -> None:
        self.record_event("mouse_move", x=x, y=y)

    def on_click(
        self, x: int, y: int, button: Any, pressed: bool
    ) -> None:
        self.record_event(
            "mouse_click",
            x=x,
            y=y,
            button=button.name,
            pressed=pressed
        )

    def on_scroll(
        self, x: int, y: int, dx: int, dy: int
    ) -> None:
        self.record_event("mouse_scroll", x=x, y=y, dx=dx, dy=dy)

    # Keyboard callbacks
    def on_press(self, key: Any) -> None:
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self.record_event("key_press", key=k)

    def on_release(self, key: Any) -> Optional[List[Dict[str, Any]]]:
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self.record_event("key_release", key=k)
        if key == keyboard.Key.esc:
            # Save under 'default'
            self.all_events['default'] = self.events
            safe_dump_to_file(self.all_events, self.events_path)
            print(f"Saved {len(self.events)} events under 'default' to {self.events_path}")
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            if self.mouse_listener:
                self.mouse_listener.stop()
            return self.events

    def _ensure_listeners(self) -> None:
        if not self.mouse_listener:
            self.mouse_listener = mouse.Listener(
                on_move=self.on_move,
                on_click=self.on_click,
                on_scroll=self.on_scroll
            )
            self.mouse_listener.start()
        if not self.keyboard_listener:
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.keyboard_listener.start()

    def start_recording(self) -> str:
        print("⏺️ Recording... Press Esc to stop and save.")
        self.start_time = now()
        self.events.clear()
        self._ensure_listeners()
        while (
            self.mouse_listener and self.mouse_listener.running and
            self.keyboard_listener and self.keyboard_listener.running
        ):
            time.sleep(0.1)
        return self.events_path

    def replay(self, event_type: str) -> None:
        records = safe_load_from_file(self.events_path) or {}
        events = records.get(event_type, [])

        stop_flag = False
        def on_abort(key: Any) -> bool:
            nonlocal stop_flag
            if key == keyboard.Key.esc:
                stop_flag = True
                return False
            return True

        abort_listener = keyboard.Listener(on_press=on_abort)
        abort_listener.start()

        gui = get_auto_gui()
        start_ts = now()
        for e in events:
            if stop_flag:
                print("Replay aborted.")
                break
            delay = e["time"] - (now() - start_ts)
            if delay > 0:
                time.sleep(delay)

            et = e["type"]
            if et == "mouse_move":
                gui.moveTo(e["x"], e["y"])
            elif et == "mouse_click":
                if e["pressed"]:
                    gui.mouseDown(
                        e["x"], e["y"], button=e.get("button", "left")
                    )
                else:
                    gui.mouseUp(
                        e["x"], e["y"], button=e.get("button", "left")
                    )
            elif et == "mouse_scroll":
                gui.scroll(
                    e.get("dy", 0), x=e.get("x", 0), y=e.get("y", 0)
                )
            elif et == "key_press":
                gui.keyDown(e["key"])
            elif et == "key_release":
                gui.keyUp(e["key"])

        abort_listener.stop()
        abort_listener.join()
        if not stop_flag:
            print("Replay finished.")


# Module API

def record_session(
    events_file: Optional[str] = None
) -> str:
    """
    Record events, then prompt for an event type and save mapping.
    """
    rec = EventsRecorder(events_path=events_file, refresh=True)
    path = rec.start_recording()
    exit_flag, event_type = get_user_input_window()
    if not exit_flag and event_type:
        all_events = safe_load_from_file(path) or {}
        default_events = all_events.get("default", [])
        all_events[event_type] = default_events
        safe_dump_to_file(all_events, path)
        print(f"Mapped 'default' events to '{event_type}' in {path}")
    return path


def replay_session(
    event_type: str,
    events_file: Optional[str] = None
) -> None:
    rec = EventsRecorder(events_path=events_file)
    rec.replay(event_type)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Record or replay GUI events")
    parser.add_argument(
        "--replay",
        help="Event type to replay"
    )
    parser.add_argument(
        "--file",
        help="Events JSON file path",
        default=None
    )
    args = parser.parse_args()

    if args.replay:
        replay_session(args.replay, args.file)
    else:
        record_session(args.file)

