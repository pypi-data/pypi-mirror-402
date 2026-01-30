from typing import List, Dict, Optional, Union, Callable
import threading
import subprocess
import re
from Xlib import X, display
from Xlib.ext import randr
from difflib import get_close_matches
from abstract_utilities import get_closest_match_from_list
class DisplayManager:
    # Command constants
    XRANDR_CMD = ['xrandr', '--query']
    WMCTRL_LIST_CMD = ['wmctrl', '-l', '-p']
    WMCTRL_MOVE_CMD = ['wmctrl', '-i', '-r']
    XDOTOOL_GEOMETRY_CMD = ['xdotool', 'getwindowgeometry']

    # Regex patterns
    MONITOR_REGEX = re.compile(r'(\S+)\s+connected\s+(\d+)x(\d+)\+(\d+)\+(\d+)')
    POSITION_REGEX = re.compile(r'Position:\s+(\d+),(\d+)')
    GEOMETRY_REGEX = re.compile(r'Geometry:\s+(\d+)x(\d+)')

    # Browser title signatures
    BROWSER_PATTERNS = [
        'Mozilla', 'Firefox', 'Google Chrome', 'Chromium',
        'Microsoft Edge', 'Opera', 'Safari'
    ]

    def __init__(self, on_monitor_change: Optional[Callable[[List[Dict]], None]] = None,
                 on_window_event: Optional[Callable[[object], None]] = None):
        """Initialize DisplayManager with optional callbacks for monitor and window events."""
        self.disp = display.Display()
        self.root = self.disp.screen().root
        self.on_monitor_change = on_monitor_change
        self.on_window_event = on_window_event
        self._running = False
        self._thread = None

        # Check for required tools
        self._check_tools(['xrandr', 'wmctrl', 'xdotool'])

        # Setup Xlib event masks
        #randr.SelectInput(self.disp, self.root, randr.RRScreenChangeNotifyMask)
        #self.root.change_attributes(event_mask=X.SubstructureNotifyMask)
        # Right: tell the X window to send RandR events
        self.root.xrandr_select_input(randr.RRScreenChangeNotifyMask)
    def _check_tools(self, tools: List[str]) -> None:
        """Verify that required tools are installed."""
        for tool in tools:
            try:
                subprocess.run([tool, '--help'], capture_output=True, check=True)
            except FileNotFoundError:
                raise RuntimeError(f"Required tool '{tool}' not installed or not found")

    def start(self) -> None:
        """Start the event loop in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._event_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the event loop."""
        self._running = False
        if self._thread:
            self._thread.join()

    def _event_loop(self) -> None:
        """Main event loop for Xlib events."""
        while self._running:
            try:
                ev = self.disp.next_event()
                if ev.type == randr.RRScreenChangeNotify:
                    monitors = self.get_monitors()
                    if self.on_monitor_change:
                        self.on_monitor_change(monitors)
                elif ev.type in (X.CreateNotify, X.ConfigureNotify, X.DestroyNotify):
                    if self.on_window_event:
                        self.on_window_event(ev)
            except Exception as e:
                print(f"Error in event loop: {e}")

    def get_monitors(self) -> List[Dict[str, Union[str, int]]]:
        """Get monitor boundaries using xrandr."""
        monitors = []
        try:
            result = subprocess.run(
                self.XRANDR_CMD, capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                m = self.MONITOR_REGEX.match(line)
                if not m:
                    continue
                name, w, h, x_off, y_off = m.groups()
                monitors.append({
                    'name': name,
                    'x': int(x_off),
                    'y': int(y_off),
                    'width': int(w),
                    'height': int(h)
                })
        except subprocess.SubprocessError as e:
            print(f"Error running xrandr: {e}")
        return monitors

    def move_window_to_monitor(self, window_id: str, monitor_name: str) -> bool:
        """Move a window to the specified monitor's top-left corner."""
        try:
            for mon in self.get_monitors():
                if mon['name'] == monitor_name:
                    x, y = mon['x'], mon['y']
                    cmd = self.WMCTRL_MOVE_CMD + [window_id, '-e', f"0,{x},{y},-1,-1"]
                    subprocess.run(cmd, check=True)
                    print(f"Moved window {window_id} to {monitor_name} ({x},{y})")
                    return True
            print(f"Monitor {monitor_name} not found")
            return False
        except subprocess.SubprocessError as e:
            print(f"Error moving window: {e}")
            return False

    def get_window_geometry(self, window_id: str) -> Optional[Dict[str, int]]:
        """Get window position (x, y) and size (width, height) using xdotool."""
        try:
            result = subprocess.run(
                self.XDOTOOL_GEOMETRY_CMD + [window_id],
                capture_output=True, text=True, check=True
            )
            pos_m = self.POSITION_REGEX.search(result.stdout)
            size_m = self.GEOMETRY_REGEX.search(result.stdout)
            if pos_m and size_m:
                return {
                    'x': int(pos_m.group(1)),
                    'y': int(pos_m.group(2)),
                    'width': int(size_m.group(1)),
                    'height': int(size_m.group(2))
                }
            return None
        except subprocess.SubprocessError as e:
            print(f"Error getting geometry: {e}")
            return None

    def get_monitor_for_window(
        self, window_id: Optional[str] = None, x: Optional[int] = None, y: Optional[int] = None
    ) -> Dict[str, Union[str, int]]:
        """Determine which monitor a given window (or coordinate) is on."""
        if window_id and (x is None or y is None):
            geom = self.get_window_geometry(window_id)
            if not geom:
                return {}
            x, y = geom['x'], geom['y']

        if x is None or y is None:
            return {}

        for mon in self.get_monitors():
            if mon['x'] <= x < mon['x'] + mon['width'] and \
               mon['y'] <= y < mon['y'] + mon['height']:
                return {
                    'monitor_name': mon['name'],
                    'monitor_details': f"{mon['width']}x{mon['height']}+{mon['x']}+{mon['y']}",
                    'win_x': x,
                    'win_y': y
                }
        return {}

    def get_window_items(
        self, windows: List[str], find_window_id: Optional[str] = None,
        find_desktop: Optional[str] = None, find_pid: Optional[str] = None,
        find_host: Optional[str] = None, find_window_title: Optional[str] = None
    ) -> Union[Dict[str, str], List[Dict[str, str]]]:
        """Parse `wmctrl -l -p` output, optionally filtering."""
        filters = {k: v for k, v in {
            'window_id': find_window_id, 'desktop': find_desktop, 'pid': find_pid,
            'host': find_host, 'window_title': find_window_title
        }.items() if v is not None}

        parsed = []
        for line in windows:
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            win_id, desktop, pid, host, title = parts
            info = {
                'window_id': win_id, 'desktop': desktop, 'pid': pid,
                'host': host, 'window_title': title
            }
            self.get_monitor_for_window(window_id=win_id)
            parsed.append(info)
            if filters and all(info[k] == v for k, v in filters.items()):
                return info
        return parsed

    def get_existing_browsers_data(
        self, title: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Find browser windows, optionally filtering by title."""
        try:
            result = subprocess.run(
                self.WMCTRL_LIST_CMD, capture_output=True, text=True, check=True
            )
            windows = result.stdout.splitlines()
        except subprocess.SubprocessError as e:
            print(f"Error running wmctrl: {e}")
            return []

        all_items = self.get_window_items(windows)
        browser_titles = [
            info['window_title']
            for info in (all_items if isinstance(all_items, list) else [all_items])
            if any(pat.lower() in info['window_title'].lower() for pat in self.BROWSER_PATTERNS)
        ]

        if title and browser_titles:
            browser_titles = get_closest_match_from_list(title, total_list=browser_titles)
            
            
        return [
            self.get_window_items(windows, find_window_title=bt)
            for bt in browser_titles
        ]
def on_monitor_change(monitors):
    print(f"Monitors changed: {monitors}")


def on_window_event(event):
    if event.type == X.CreateNotify:
        print(f"New window: {event.window.id}")
    elif event.type == X.ConfigureNotify:
        print(f"Window {event.window.id} moved/resized to {event.width}x{event.height} @ {event.x},{event.y}")
    elif event.type == X.DestroyNotify:
        print(f"Window destroyed: {event.window.id}")
dm = DisplayManager(on_monitor_change, on_window_event)
dm.start()

# Move a window to a monitor
dm.move_window_to_monitor("0x123456", "HDMI-1")

# Get browser windows
browsers = dm.get_existing_browsers_data(title="chatgpt")
print(browsers)

# Stop the manager
dm.stop()
