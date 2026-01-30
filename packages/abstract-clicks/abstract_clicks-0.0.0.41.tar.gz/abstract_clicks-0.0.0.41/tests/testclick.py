from abstract_utilities import SingletonMeta,os,safe_dump_to_file
from src.abstract_clicks import get_time_span,get_events_path,pyautogui,get_events_recorder,mouse,keyboard,get_time

from abstract_gui import getUserInputwindow
prompt="please enter the event type"
title="event type"
exitcall, event_type = getUserInputwindow(prompt=prompt,
                                          title=title)

# ——— GUI prompt (deferred import) ———
class eventsRecorder(metaclass=SingletonMeta):
    def __init__(self,
                 events_path=None,
                 events=None,
                 all_events=None,
                 start_time=None
                 ):
        if not hasattr(self, 'initialized') or self.initialized == False:
            self.initialized = True
            self.all_events = all_events or {}
            self.events = events or []
            self.start_time = start_time or get_time()
            self.events_path = get_events_path(events_path,
                                              default="session.json")
            self.last_trigger = None
    def record_event(self,evt_type: str, **data):
        self.last_trigger = 'record_event'
        """Append a timestamped event dict to events."""
        self.events.append({
            "time": get_time_span(self.start_time),
            "type": evt_type,
            **data
        })

    # ——— Mouse callbacks ———
    def on_move(self,x, y):
        self.last_trigger = 'on_move'
        self.record_event("mouse_move", x=x, y=y)

    def on_click(self,x, y, button, pressed):
        self.last_trigger = 'on_click'
        self.record_event(
            "mouse_click",
            x=x, y=y,
            button=button.name,
            pressed=pressed
        )

    def on_scroll(self,x, y, dx, dy):
        self.last_trigger = 'on_scroll'
        self.record_event("mouse_scroll", x=x, y=y, dx=dx, dy=dy)

    # ——— Keyboard callbacks ———
    def on_press(self,key):
        self.last_trigger = 'on_press'
        try:
            k = key.char
        except AttributeError:
            k = str(key)    
        self.record_event("key_press", key=k)

    def on_release(self,key):
        
        if self.last_trigger != 'on_release':
            self.last_trigger = 'on_release'
            input(self.last_trigger)
            try:
                k = key.char
            except AttributeError:
                k = str(key)
            self.record_event("key_release", key=k)
            # Stop recording on Esc
            if key == keyboard.Key.esc:
                input(key == keyboard.Key.esc)
                # Write out JSON and stop both listeners
                prompt="please enter the event type"
                title="event type"
                exitcall, event_type = getUserInputwindow(prompt=prompt,
                                                          title=title)
                self.all_events[event_type] = self.events
                safe_dump_to_file(data = self.all_events,
                                  file_path = self.events_path)
                self.events = []
                print(f"Recorded {len(self.events)} events → {self.events_path}")
                if exitcall:
                    self.keyboard_listener.stop()
                    self.mouse_listener.stop()
def get_events_recorder(events_path=None,
                        refresh=False,
                        all_events=None,
                        start_time=None
                        ):
    if refresh:
        rec = eventsRecorder()
        rec.initialized = False
    rec = eventsRecorder(all_events=all_events,
                          start_time=start_time,
                          events_path=events_path)
    return rec

def replay_actions(event_type,
                   refresh=False,
                   events_path=None,
                   all_events=None,
                   start_time=None):
    rec = get_events_recorder(refresh=refresh,
                              all_events=all_events,
                              start_time=start_time,
                              events_path=events_path)
    events_path = rec.events_path
    events_record = safe_load_from_file(events_path)
    events = events_record.get(event_type)
    start = time.time()
    for e in events:
        # wait until it's time for this event
        delay = e["time"] - (time.time() - start)
        if delay > 0:
            time.sleep(delay)
        et = e["type"]
        if et == "mouse_move":
            pyautogui.moveTo(e["x"], e["y"])
        elif et == "mouse_click":
            btn = e.get("button", "left")
            if e["pressed"]:
                pyautogui.mouseDown(e["x"], e["y"], button=btn)
            else:
                pyautogui.mouseUp(e["x"], e["y"], button=btn)
        elif et == "mouse_scroll":
            pyautogui.scroll(e["dy"], x=e["x"], y=e["y"])
        elif et == "key_press":
            pyautogui.keyDown(e["key"])
        elif et == "key_release":
            pyautogui.keyUp(e["key"])
def start_recording(events_path=None,
                    refresh=False,
                   all_events=None,
                   start_time=None):
    print("⏺️  Recording… Press Esc to stop and save session.json")
    rec = get_events_recorder(events_path=events_path,
                              refresh=refresh,
                              all_events=all_events,
                              start_time=start_time,
                              )
    # Create listeners
    ml = mouse.Listener(
        on_move=rec.on_move,
        on_click=rec.on_click,
        on_scroll=rec.on_scroll
    )
    kl = keyboard.Listener(
        on_press=rec.on_press,
        on_release=rec.on_release
    )

    # Give the recorder references so it can stop them
    rec.mouse_listener = ml
    rec.keyboard_listener = kl

    # Start and block until stop()
    ml.start()
    kl.start()
    ml.join()
    kl.join()
start_recording()
