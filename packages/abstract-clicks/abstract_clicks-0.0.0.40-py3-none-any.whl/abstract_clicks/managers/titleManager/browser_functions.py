
import subprocess
import platform
import psutil
import webbrowser
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from abstract_webtools import get_soup
from abstract_utilities import write_to_file, read_from_file
import uuid
import platform
import platform
import subprocess
import psutil
import time
import pyautogui
import subprocess
import re
from .titleManager import get_titlemanager
titlemanager = get_titlemanager()
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
if platform.system() == 'Windows':
    import win32gui
    import win32con
elif platform.system() == 'Darwin':  # macOS
    try:
        from AppKit import NSScreen, NSWorkspace
    except ImportError:
        NSScreen = NSWorkspace = None



def get_html_content(html_content=None, title="My Permanent Tab"):
    """Generate default HTML content if none provided."""
    html_cont = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
        </head>
        <body>
            <h1>{title}</h1>
            <p>This is a programmatically opened tab with a permanent title.</p>
        </body>
        </html>
    """
    return html_content or html_cont



def get_browser_url_from_pid(pid):
    """Placeholder for inferring URL from PID."""
    try:
        process = psutil.Process(int(pid))
        return None  # Implement with Chrome DevTools if needed
    except psutil.NoSuchProcess:
        return None
import subprocess

def get_existing_browser_info(title=None, url=None):
    """Find a browser window on Linux using wmctrl."""
    try:
        # Run wmctrl to list windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, check=True)
        windows = result.stdout.splitlines()

        # Find matching window
        for line in windows:
            # wmctrl -l format: <window_id> <desktop> <host> <title>
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            window_id, _, _, window_title = parts
            if title and title.lower() in window_title.lower():
                return {
                    "window_id": window_id,
                    "title": window_title,
                    "url": "",  # URL not accessible
                    "html": "",  # HTML not accessible
                    "soup": None,  # No HTML parsing
                    "tab_index": 0  # Tab index not accessible
                }

        print(f"No browser window found with title: {title}")
        return {}

    except FileNotFoundError:
        print("wmctrl not installed or not found")
        return {}
    except subprocess.SubprocessError as e:
        print(f"Error running wmctrl: {e}")
        return {}
def get_browser_coordinates(url=None, title=None, browser_title=None, window_id=None):
    """Get the coordinates of a browser window."""
    
    return titlemanager.get_window_coordinates(url=url, title=title, browser_title=browser_title, window_id=window_id)
def control_browser_window(window_id, action):
    """
    Control the state of a browser window (maximize or minimize).
    
    Args:
        window_id (str): Window ID from get_existing_browsers_info.
        action (str): 'maximize' or 'minimize'.
    """
    try:
        if action == 'maximize':
            subprocess.run([
                'wmctrl', '-i', '-r', window_id,
                '-b', 'add,maximized_vert,maximized_horz'
            ], check=True)
            print(f"Maximized window {window_id}")
            return True
        elif action == 'minimize':
            subprocess.run(['xdotool', 'windowminimize', window_id], check=True)
            print(f"Minimized window {window_id}")
            return True
        else:
            print(f"Invalid action: {action}")
            return False

    except FileNotFoundError as e:
        print(f"Required tool not found: {e}")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error controlling window: {e}")
        return False
def open_devtools(driver=None, window_id=None):
    """Open the browser's developer tools."""
    try:
        if driver:
            # Use Chrome DevTools Protocol to open DevTools
            driver.execute_cdp_cmd("Page.enable", {})
            driver.execute_cdp_cmd("Inspector.enable", {})
            driver.execute_cdp_cmd("Inspector.activate", {})
            print("DevTools opened via Selenium CDP")
            return True
        elif window_id and platform.system() == 'Linux':
            subprocess.run(['xdotool', 'windowactivate', window_id])
            subprocess.run(['xdotool', 'key', 'ctrl+shift+i'])  # Ctrl+Shift+I for DevTools
            print("DevTools opened via xdotool")
            return True
        elif window_id and platform.system() == 'Windows' and win32gui:
            win32gui.SetForegroundWindow(int(window_id))
            import pyautogui
            pyautogui.hotkey('ctrl', 'shift', 'i')
            print("DevTools opened via pyautogui")
            return True
        elif window_id and platform.system() == 'Darwin':
            script = f'''
            tell application "Google Chrome"
                activate
                tell application "System Events"
                    keystroke "t" using {{command down, option down}}
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', script])  # Cmd+Opt+I for DevTools
            print("DevTools opened via AppleScript")
            return True
        print("Unable to open DevTools")
        return False
    except Exception as e:
        print(f"Error opening DevTools: {e}")
        return False


def get_browser_tab_and_index(url=None, title=None):
    """Get tab info and index using comprehensive matching."""
    try:
     
        # Create or retrieve title info
        title_info = titlemanager.make_title(title=title, url=url,open_browser=True)
        if not title_info:
            print("Failed to create title info")
            return {"title_info": {}, "tab_index": None}

        # Find tab with comprehensive criteria
        tab_info = titlemanager.find_tab(
            url=title_info.get("url"),
            title=title_info.get("title"),
            browser_title=title_info.get("browser_title"),
            window_id=title_info.get("window_id"),
            pid=title_info.get("pid")
        )
        if not tab_info:
            print("No matching tab found")
            return {"title_info": title_info, "tab_index": None}

        # Switch to the tab
        switch_result = titlemanager.switch_window(
            url=tab_info.get("url"),
            title=tab_info.get("title"),
            browser_title=tab_info.get("browser_title"),
            window_id=tab_info.get("window_id"),
            pid=tab_info.get("pid")
        )
        if not switch_result:
            print("Failed to switch to tab")
            return {"title_info": tab_info, "tab_index": tab_info.get("tab_index")}

        return {"title_info": tab_info, "tab_index": tab_info.get("tab_index")}
    except Exception as e:
        print(f"Error in get_browser_tab_and_index: {e}")
        return {"title_info": {}, "tab_index": None}
  # For fallback mouse/keyboard simulation

def open_browser_tab(self, url=None, title="My Permanent Tab", html_file_path=None, html_content=None, duplicate=False, fullscreen=False, inspect=False):
        """Open a new browser tab or return existing window info, with optional full screen and inspect."""
        try:
            soup = call_soup(url=url)
            browser_title = get_title(soup=soup)
            info = self.find_tab(url=url, title=title, browser_title=browser_title)
            if info and not duplicate:
                if fullscreen:
                    set_browser_fullscreen(window_id=info.get("window_id"), fullscreen=fullscreen)
                if inspect:
                    open_devtools(window_id=info.get("window_id"))
                return info

            html_content = get_html_content(html_content=html_content, title=title)
            if html_content and html_file_path:
                write_to_file(contents=html_content, file_path=html_file_path)
                url = url or f"file://{html_file_path}"

            # Use Selenium for precise control
            chrome_options = Options()
            driver = None
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                info = {
                    "window_id": driver.current_window_handle,
                    "title": driver.title,
                    "url": driver.current_url,
                    "html": driver.page_source,
                    "soup": BeautifulSoup(driver.page_source, 'html.parser'),
                    "tab_index": driver.window_handles.index(driver.current_window_handle),
                    "pid": str(psutil.Process().pid) if psutil else None
                }
                if fullscreen:
                    set_browser_fullscreen(driver=driver, fullscreen=fullscreen)
                if inspect:
                    open_devtools(driver=driver)
            except Exception as e:
                print(f"Selenium failed, falling back to webbrowser: {e}")
                webbrowser.open_new_tab(url)
                time.sleep(1.0)  # Wait for tab to open
                info = self.find_tab(url=url, title=title, browser_title=browser_title)
                if fullscreen and info.get("window_id"):
                    set_browser_fullscreen(window_id=info.get("window_id"), fullscreen=fullscreen)
                if inspect and info.get("window_id"):
                    open_devtools(window_id=info.get("window_id"))

            if driver:
                driver.quit()
            return info
        except Exception as e:
            print(f"Error opening browser tab: {e}")
            return {"window_id": None, "title": title, "pid": None, "url": url, "tab_index": None}
def get_browser_url_from_pid(pid):
    """Attempt to infer the URL from a browser process (simplified)."""
    try:
        process = psutil.Process(int(pid))
        # This is a placeholder; actual URL extraction requires browser-specific APIs
        # For example, use Selenium or browser debugging protocols
        return None  # Replace with actual logic if available
    except psutil.NoSuchProcess:
        return None


