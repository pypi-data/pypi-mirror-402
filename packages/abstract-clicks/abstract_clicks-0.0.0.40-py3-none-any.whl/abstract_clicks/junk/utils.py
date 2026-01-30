from ..utils import *
from ..managers.importClasses import *
# Lazy-loaded modules
auto_gui: Any = None
_user_input_window: Any = None
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
            self.default_events_path = os.path.join(abs_dir(),'default_events.json')
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
            safe_dump_to_file(self.all_events, self.default_events_path)
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
        return self.default_events_path


    def _preprocess_events(self, events: List[Dict], speed_factor: float, min_move_distance: float) -> List[Dict]:
        """Preprocess events to set target times and filter small mouse movements."""
        processed_events = []
        last_x, last_y = None, None

        for e in events:
            # Create a copy of the event with adjusted target time
            event = e.copy()
            event['target_time'] = e['time'] / speed_factor
            
            # Filter mouse_move events based on distance
            if event['type'] == 'mouse_move':
                x, y = event['x'], event['y']
                event['x'] = uniform(x*.995, x*1.005)
                event['y'] = uniform(y*.995, y*1.005)
                if last_x is not None and last_y is not None:
                    distance = math.sqrt((event['x'] - last_x)**2 + (event['y'] - last_y)**2)
                    if distance < uniform(min_move_distance*.995, min_move_distance*1.005):
                        continue
                last_x, last_y = x, y
            elif event['type'] in ['mouse_click', 'mouse_scroll']:
                last_x, last_y = event.get('x'), event.get('y')

            processed_events.append(event)

        return processed_events
    def replay(self, event_type: str, speed_factor: float = 11.0, min_move_distance: float = 50) -> None:
        records = safe_load_from_file(self.events_path) or {}
        events = records.get(event_type, [])

        if not events:
            print(f"No events found for event_type '{event_type}' in {self.events_path}")
            return

        # Preprocess events to set target times and filter movements
        processed_events = self._preprocess_events(events, speed_factor, min_move_distance)
        print(f"Replaying {len(processed_events)} events (filtered from {len(events)})")

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

        for e in processed_events:
            if stop_flag:
                print("Replay aborted.")
                break

            # Wait until the target time is reached
            target_time = e['target_time']
            elapsed = now() - start_ts
            delay = target_time - elapsed

            if delay > 0:
                time.sleep(delay)

            et = e['type']
            if et == 'mouse_move':
                gui.moveTo(e['x'], e['y'])
            elif et == 'mouse_click':
                if e['pressed']:
                    gui.mouseDown(
                        e['x'], e['y'], button=e.get('button', 'left')
                    )
                else:
                    gui.mouseUp(
                        e['x'], e['y'], button=e.get('button', 'left')
                    )
            elif et == 'mouse_scroll':
                gui.scroll(
                    e.get('dy', 0), x=e.get('x', 0), y=e.get('y', 0)
                )
            elif et == 'key_press':
                gui.keyDown(e['key'])
            elif et == 'key_release':
                gui.keyUp(e['key'])

        abort_listener.stop()
        abort_listener.join()
        if not stop_flag:
            print("Replay finished.")




