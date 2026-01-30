from ...imports import *

from abstract_utilities import write_to_file
import pathlib
import subprocess
import platform
import psutil
from abstract_webtools import get_soup
from abstract_utilities import write_to_file
import webbrowser
import time
from abstract_webtools import get_soup,get_date
from ..utils import *
def is_window_open(url=None, title=None, browser_title=None):
    """Check if a window exists with the given title, browser title, or URL."""
    titles = [t for t in [title, browser_title] if t]
    if not titles and not url:
        return {}

    if platform.system() == 'Linux' and titles:
        try:
            for t in titles:
                result = subprocess.run(
                    ['xdotool', 'search', '--name', t],
                    capture_output=True, text=True
                )
                wids = [w for w in result.stdout.split() if w.strip()]
                if wids:
                    wid = wids[-1]
                    real_title = subprocess.run(
                        ['xdotool', 'getwindowname', wid],
                        capture_output=True, text=True
                    ).stdout.strip()
                    pid = subprocess.run(
                        ['xdotool', 'getwindowpid', wid],
                        capture_output=True, text=True
                    ).stdout.strip()
                    url = get_browser_url_from_pid(pid) or url or 'Unknown'
                    return {
                        'window_id': wid,
                        'title': real_title,
                        'pid': pid,
                        'url': url,
                        'html': None,
                        'soup': None
                    }
            print(f"No window found with titles: {titles}")
            return {}
        except Exception as e:
            print(f"Error finding window on Linux: {e}")
            return {}
    elif platform.system() == 'Windows' and win32gui:
        try:
            def callback(hwnd, windows):
                window_title = win32gui.GetWindowText(hwnd).lower()
                for t in titles:
                    if t.lower() in window_title:
                        windows.append((hwnd, window_title))
            windows = []
            win32gui.EnumWindows(callback, windows)
            if windows:
                hwnd, real_title = windows[0]
                return {
                    'window_id': str(hwnd),
                    'title': real_title,
                    'pid': None,
                    'url': url or 'Unknown',
                    'html': None,
                    'soup': None
                }
            print(f"No window found with titles: {titles}")
            return {}
        except Exception as e:
            print(f"Error finding window on Windows: {e}")
            return {}
    elif platform.system() == 'Darwin' and NSWorkspace:
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_apps = workspace.runningApplications()
            for app in active_apps:
                for t in titles:
                    if t.lower() in app.localizedName().lower():
                        return {
                            'window_id': str(app.processIdentifier()),
                            'title': app.localizedName(),
                            'pid': str(app.processIdentifier()),
                            'url': url or 'Unknown',
                            'html': None,
                            'soup': None
                        }
            print(f"No window found with titles: {titles}")
            return {}
        except Exception as e:
            print(f"Error finding window on macOS: {e}")
            return {}
    else:
        return get_existing_browser_info(title=titles[0] if titles else None, url=url)
def get_window_coordinates(self, url=None, title=None, browser_title=None, window_id=None):
    """Determine the coordinates and size of a browser window."""
    try:
        # Find the tab
        info = self.find_tab(url=url, title=title, browser_title=browser_title, window_id=window_id)
        if not info or not info.get("window_id"):
            print("No window found for coordinates")
            return {"x": None, "y": None, "width": None, "height": None}

        # Use Selenium if window_id is a Selenium handle
        if "CDwindow" in info.get("window_id"):
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            driver = None
            try:
                driver = webdriver.Chrome(options=chrome_options)
                if info.get("window_id") in driver.window_handles:
                    driver.switch_to.window(info.get("window_id"))
                    window_size = driver.get_window_size()
                    window_position = driver.get_window_position()
                    return {
                        "x": window_position.get("x"),
                        "y": window_position.get("y"),
                        "width": window_size.get("width"),
                        "height": window_size.get("height")
                    }
                print(f"Window ID {info.get('window_id')} not found in Selenium")
                return {"x": None, "y": None, "width": None, "height": None}
            except Exception as e:
                print(f"Selenium error getting coordinates: {e}")
                return {"x": None, "y": None, "width": None, "height": None}
            finally:
                if driver:
                    driver.quit()

        # Platform-specific coordinate retrieval
        if platform.system() == 'Linux' and info.get("window_id"):
            try:
                result = subprocess.run(
                    ['xdotool', 'getwindowgeometry', info.get("window_id")],
                    capture_output=True, text=True
                )
                lines = result.stdout.splitlines()
                for line in lines:
                    if "Position" in line:
                        pos = line.split(":")[1].split("(")[0].strip()
                        x, y = map(int, pos.split(","))
                    if "Geometry" in line:
                        geom = line.split(":")[1].strip()
                        width, height = map(int, geom.split("x"))
                return {"x": x, "y": y, "width": width, "height": height}
            except Exception as e:
                print(f"Error getting coordinates on Linux: {e}")
                return {"x": None, "y": None, "width": None, "height": None}
        elif platform.system() == 'Windows' and win32gui and info.get("window_id"):
            try:
                rect = win32gui.GetWindowRect(int(info.get("window_id")))
                return {
                    "x": rect[0],
                    "y": rect[1],
                    "width": rect[2] - rect[0],
                    "height": rect[3] - rect[1]
                }
            except Exception as e:
                print(f"Error getting coordinates on Windows: {e}")
                return {"x": None, "y": None, "width": None, "height": None}
        elif platform.system() == 'Darwin' and NSWorkspace and info.get("pid"):
            try:
                script = f'''
                tell application "System Events"
                    tell process id {info.get("pid")}
                        set {{x, y}} to position of front window
                        set {{width, height}} to size of front window
                        return {{x, y, width, height}}
                    end tell
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                x, y, width, height = map(int, result.stdout.strip().split(","))
                return {"x": x, "y": y, "width": width, "height": height}
            except Exception as e:
                print(f"Error getting coordinates on macOS: {e}")
                return {"x": None, "y": None, "width": None, "height": None}
        print("Unsupported platform or missing window ID")
        return {"x": None, "y": None, "width": None, "height": None}
    except Exception as e:
        print(f"Error getting window coordinates: {e}")
        return {"x": None, "y": None, "width": None, "height": None}
    return {}

def move_window_with_mouse(pid=None, title=None, monitor_index=1, *args, **kwargs):
    try:
        monitors = get_monitors()
        if not monitors or monitor_index < 1 or monitor_index > len(monitors):
            print(f"Invalid monitor index: {monitor_index}. Available monitors: {len(monitors)}")
            return False

        target_monitor = monitors[monitor_index - 1]
        x, y = target_monitor['x'] + 50, target_monitor['y'] + 50
        print(f"Moving window to monitor {monitor_index}: x={x}, y={y}")

        if platform.system() == 'Linux' and (pid or title):
            if pid:
                result = subprocess.run(['xdotool', 'search', '--pid', str(pid)], capture_output=True, text=True)
            elif title:
                result = subprocess.run(['xdotool', 'search', '--name', title], capture_output=True, text=True)
            else:
                print("PID or title required for Linux")
                return False

            window_ids = result.stdout.strip().split()
            if not window_ids:
                print(f"No window found for PID: {pid} or title: {title}")
                return False

            window_id = window_ids[0]
            if not window_id.isdigit():
                print(f"Invalid window ID: {window_id}")
                return False

            subprocess.run(['xdotool', 'windowactivate', window_id])
            time.sleep(0.5)

            # Get window geometry
            result = subprocess.run(['xdotool', 'getwindowgeometry', window_id], capture_output=True, text=True)
            output = result.stdout
            position_line = [line for line in output.split('\n') if 'Position' in line]
            if not position_line:
                print(f"No position information for window {window_id}")
                return False

            position_str = position_line[0].split(': ')[1].split(' ')[0].strip()
            try:
                win_x, win_y = map(int, position_str.split(','))
            except ValueError as e:
                print(f"Error parsing position '{position_str}': {e}")
                return False

            pyautogui.moveTo(win_x + 50, win_y + 20)
            pyautogui.mouseDown(button='left')
            time.sleep(0.2)
            pyautogui.moveTo(x, y, duration=1)
            pyautogui.mouseUp(button='left')
            print(f"Dragged window {window_id} to monitor {monitor_index} at x={x}, y={y}")
            return True
        else:
            print(f"Unsupported platform: {platform.system()} or missing PID/title")
            return False
    except Exception as e:
        print(f"Error moving window with mouse: {e}")
        return False

def get_monitors():
    """Get list of monitors with their coordinates and dimensions."""
    if platform.system() == 'Windows':
        import win32api
        monitors = []
        def monitor_enum_callback(hmonitor, hdc, lprc, dwData):
            monitors.append({
                'x': lprc.left, 'y': lprc.top,
                'width': lprc.right - lprc.left, 'height': lprc.bottom - lprc.top
            })
            return True
        win32api.EnumDisplayMonitors(None, None, monitor_enum_callback, 0)
        return monitors

    elif platform.system() == 'Linux':
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            monitors = []
            for line in result.stdout.splitlines():
                if ' connected' in line:
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and '+' in part:
                            width, height = get_dimensions(part)  # Parse '2560x1440+0+0'
                            if width is None or height is None:
                                continue
                            x, y = map(int, [part.split('+')[1], parts[parts.index(part) + 1]])
                            monitors.append({'x': x, 'y': y, 'width': width, 'height': height})
                            break
            return monitors
        

    elif platform.system() == 'Darwin':
        if NSScreen is None:
            print("macOS support requires PyObjC. Install with 'pip install pyobjc'.")
            return []
        screens = NSScreen.screens()
        return [
            {
                'x': int(screen.frame().origin.x),
                'y': int(screen.frame().origin.y),
                'width': int(screen.frame().size.width),
                'height': int(screen.frame().size.height)
            }
            for screen in screens
        ]

    return []
def move_window_with_mouse(pid=None, title=None, monitor_index=1, *args, **kwargs):
    try:
        monitors = get_monitors()
        if not monitors or monitor_index < 1 or monitor_index > len(monitors):
            print(f"Invalid monitor index: {monitor_index}. Available monitors: {len(monitors)}")
            return False

        target_monitor = monitors[monitor_index - 1]
        x, y = target_monitor['x'] + 50, target_monitor['y'] + 50
        print(f"Moving window to monitor {monitor_index}: x={x}, y={y}")

        if platform.system() == 'Linux' and (pid or title):
            if pid:
                result = subprocess.run(['xdotool', 'search', '--pid', str(pid)], capture_output=True, text=True)
            elif title:
                result = subprocess.run(['xdotool', 'search', '--name', title], capture_output=True, text=True)
            else:
                print("PID or title required for Linux")
                return False

            window_ids = result.stdout.strip().split()
            if not window_ids:
                print(f"No window found for PID: {pid} or title: {title}")
                return False

            window_id = window_ids[0]
            subprocess.run(['xdotool', 'windowactivate', window_id])
            time.sleep(0.5)

            # Get window geometry
            result = subprocess.run(['xdotool', 'getwindowgeometry', window_id], capture_output=True, text=True)
            output = result.stdout
            position_line = [line for line in output.split('\n') if 'Position' in line]
            if not position_line:
                print(f"No position information for window {window_id}")
                return False

            position_str = position_line[0].split(': ')[1].split(' ')[0]
            try:
                win_x, win_y = map(int, position_str.split(','))
            except ValueError as e:
                print(f"Error parsing position '{position_str}': {e}")
                return False

            pyautogui.moveTo(win_x + 50, win_y + 20)
            pyautogui.mouseDown(button='left')
            time.sleep(0.2)
            pyautogui.moveTo(x, y, duration=1)
            pyautogui.mouseUp(button='left')
            print(f"Dragged window {window_id} to monitor {monitor_index} at x={x}, y={y}")
            return True
        else:
            print(f"Unsupported platform: {platform.system()} or missing PID/title")
            return False
    except Exception as e:
        print(f"Error moving window with mouse: {e}")
        return False
def get_window_monitor(self, window_id):
    """Determine which monitor a window resides in based on its position."""
    try:
        # Get window geometry using xdotool
        result = subprocess.run(
            ['xdotool', 'getwindowgeometry', window_id],
            capture_output=True, text=True
        )
        output = result.stdout
        # Parse position (e.g., "Position: 1920,100")
        position_line = [line for line in output.split('\n') if 'Position' in line][0]
        x, y = map(int, position_line.split(': ')[1].split(' ')[0].split(','))

        # Get monitor information using mss
        with mss.mss() as sct:
            monitors = sct.monitors[1:]  # Skip monitor 0 (combined desktop)
            for index, monitor in enumerate(monitors, 1):
                left = monitor['left']
                top = monitor['top']
                right = left + monitor['width']
                bottom = top + monitor['height']
                # Check if window's top-left corner is within monitor bounds
                if left <= x < right and top <= y < bottom:
                    print(f"Window {window_id} is on monitor {index}: {monitor}")
                    return index, monitor
            print(f"Window {window_id} not found on any monitor.")
            return None, None
    except Exception as e:
        print(f"Error determining monitor for window {window_id}: {e}")
        return None, None
def screenshot_specific_screen(output_file="new_screen.png", monitor_index=1):
    """Capture a screenshot of a specific monitor."""
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            if monitor_index < 1 or monitor_index >= len(monitors):
                print(f"Invalid monitor index: {monitor_index}. Available monitors: {len(monitors)-1}")
                return None
            monitor = monitors[monitor_index]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            img.save(output_file)
            print(f"Saved screenshot of monitor {monitor_index} to: {output_file}")
            return monitor  # Return monitor info for coordinate adjustment
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None


def switch_window(self, title=None, url=None, browser_title=None, window_id=None, pid=None,*args, **kwargs):
    """Switch focus to a window by multiple criteria."""
    try:
        # Find tab using comprehensive search
        info = self.find_tab(url=url, title=title, browser_title=browser_title, window_id=window_id, pid=pid)
        if not info:
            print(f"No window found with criteria: title={title}, url={url}, browser_title={browser_title}")
            return False

        # Use Selenium for precise window switching if window_id is available
        if info.get("window_id") and "CDwindow" in info.get("window_id"):  # Selenium window handle
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            driver = None
            try:
                driver = webdriver.Chrome(options=chrome_options)
                if info.get("window_id") in driver.window_handles:
                    driver.switch_to.window(info.get("window_id"))
                    print(f"Switched to window: {info.get('title')}")
                    return info
                print(f"Window ID {info.get('window_id')} not found in Selenium")
            except Exception as e:
                print(f"Error with Selenium switch: {e}")
            finally:
                if driver:
                    driver.quit()

        # Platform-specific switching
        if platform.system() == 'Linux' and (title or info.get("title")):
            result = subprocess.run(
                ['xdotool', 'search', '--name', title or info.get("title")],
                capture_output=True, text=True
            )
            window_ids = result.stdout.strip().split()
            if window_ids:
                subprocess.run(['xdotool', 'windowactivate', window_ids[0]])
                print(f"Switched to window: {title or info.get('title')}")
                return info
            print(f"No window found: {title or info.get('title')}")
            return False
        elif platform.system() == 'Windows' and win32gui and (title or info.get("title")):
            def callback(hwnd, target):
                if (title or info.get("title")).lower() in win32gui.GetWindowText(hwnd).lower():
                    win32gui.SetForegroundWindow(hwnd)
                    return False
            win32gui.EnumWindows(callback, None)
            print(f"Switched to window: {title or info.get('title')}")
            return info
        elif platform.system() == 'Darwin' and NSWorkspace and (title or info.get("title")):
            workspace = NSWorkspace.sharedWorkspace()
            for app in workspace.runningApplications():
                if (title or info.get("title")).lower() in app.localizedName().lower():
                    app.activateWithOptions_(0)
                    print(f"Switched to window: {title or info.get('title')}")
                    return info
            print(f"No window found: {title or info.get('title')}")
            return False
        else:
            print("Unsupported platform for window switching")
            return False
    except Exception as e:
        print(f"Error switching window: {e}")
        return False
