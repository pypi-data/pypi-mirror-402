from ...imports import *
from threading import Event
import time
from pynput import keyboard, mouse


def replay_actions(
    event_type: str,
    *,
    events_path: str | None = None,
    start_time: float | None = None,
) -> bool:
    """
    Replay recorded pynput events.
    Returns True if aborted by user (ESC).
    """

    events_path = get_events_path(path=events_path)
    events_record = safe_load_from_file(events_path)
    events = events_record.get(event_type, [])

    if not events:
        print(f"No events found for type: {event_type}")
        return False

    stop_event = Event()

    kb_controller = keyboard.Controller()
    mouse_controller = mouse.Controller()

    # ─────────────────────────────────────────────
    # Abort listener
    # ─────────────────────────────────────────────
    def on_press(key):
        if key == keyboard.Key.esc:
            stop_event.set()
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    start_ts = start_time or time.time()

    try:
        for e in events:
            if stop_event.is_set():
                print("Replay aborted by user (ESC).")
                return True

            delay = e["time"] - (time.time() - start_ts)
            if delay > 0:
                time.sleep(delay)

            _dispatch_pynput_event(e, kb_controller, mouse_controller)

    finally:
        listener.stop()

    return False
