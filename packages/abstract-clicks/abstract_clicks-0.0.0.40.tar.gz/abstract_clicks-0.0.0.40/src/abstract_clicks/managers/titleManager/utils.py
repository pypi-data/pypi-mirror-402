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
from .titleManager import *
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
# Conditional imports for platform-specific modules
if platform.system() == 'Windows':
    import win32gui
    import win32con
elif platform.system() == 'Darwin':  # macOS
    try:
        from AppKit import NSScreen, NSWorkspace
    except ImportError:
        NSScreen = NSWorkspace = None

def call_soup(url=None, soup=None):
    """Retrieve BeautifulSoup object for a URL or return existing soup."""
    if url and not soup:
        soup = get_soup(url)
    return soup

def get_title(url=None, soup=None):
    """Extract the title from a URL or BeautifulSoup object."""
    try:
        soup = call_soup(url=url, soup=soup)
        if not soup:
            return ""
        title_tag = soup.find("title")
        if not title_tag:
            return ""
        title = str(title_tag).split('>')[1].split('<')[0]
        return title.strip()
    except Exception as e:
        print(f"Error getting title: {e}")
        return ""

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

def get_existing_browser_info(title=None, url=None):
    """Find an existing browser window and its details without Selenium."""
    try:
        # Find windows with matching title
        windows = []
        if platform.system() == "Windows":
            # Note: pyautogui doesn't directly list windows; this is a simplified approach
            pyautogui.getWindowsWithTitle(title) if title else []
        elif platform.system() == "Darwin":  # macOS
            # Limited window detection on macOS
            windows = [w for w in pyautogui.getAllTitles() if title and title.lower() in w.lower()]
        else:
            print("Unsupported platform")
            return {}

        if not windows:
            print(f"No browser window found with title: {title}")
            return {}

        # Assume the first matching window is the target
        target_window = windows[0]

        # Fetch page content if URL is provided
        page_info = {}
        if url:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                page_info = {
                    "title": target_window,  # Approximation, not exact browser title
                    "url": url,
                    "html": response.text,
                    "soup": BeautifulSoup(response.text, 'html.parser'),
                    "tab_index": 0  # No tab index without browser control
                }
            except requests.RequestException as e:
                print(f"Error fetching URL: {e}")
                return {}

        return page_info

    except Exception as e:
        print(f"Error: {e}")
        return {}
def get_browser_coordinates(url=None, title=None, browser_title=None, window_id=None):
    """Get the coordinates of a browser window."""
    titlemanager = titleManager()
    return titlemanager.get_window_coordinates(url=url, title=title, browser_title=browser_title, window_id=window_id)
def set_browser_fullscreen(driver=None, window_id=None, fullscreen=False):
        """Set the browser to full screen or maximized state."""
        try:
            if fullscreen and driver:
                driver.fullscreen_window()  # Selenium full-screen mode
                print("Browser set to full screen via Selenium")
                return True
            elif fullscreen and window_id and platform.system() == 'Linux':
                subprocess.run(['xdotool', 'windowactivate', window_id])
                subprocess.run(['xdotool', 'key', 'F11'])  # Simulate F11 for full screen
                print("Browser set to full screen via xdotool")
                return True
            elif fullscreen and platform.system() == 'Windows' and win32gui and window_id:
                win32gui.ShowWindow(int(window_id), 3)  # SW_MAXIMIZE
                print("Browser maximized via pywin32")
                return True
            elif fullscreen and platform.system() == 'Darwin' and NSWorkspace:
                # macOS: Use AppleScript to toggle full screen
                script = f'''
                tell application "Google Chrome"
                    activate
                    tell front window
                        set isFullScreen to not (get is fullscreen)
                        set fullscreen to isFullScreen
                    end tell
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                print("Browser set to full screen via AppleScript")
                return True
            return False
        except Exception as e:
            print(f"Error setting full screen: {e}")
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


def get_browser_tab_and_index(url, title):
    """Get tab info and index using comprehensive matching."""
    try:
        title_mgr = titleManager()
        # Create or retrieve title info
        title_info = title_mgr.make_title(title=title, url=url,open_browser=True)
        if not title_info:
            print("Failed to create title info")
            return {"title_info": {}, "tab_index": None}

        # Find tab with comprehensive criteria
        tab_info = title_mgr.find_tab(
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
        switch_result = title_mgr.switch_window(
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

def open_browser_tab(url=None, title="My Permanent Tab", html_file_path=None, html_content=None, duplicate=False, fullscreen=False, inspect=False):
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
def get_existing_browser_info(title=None, url=None):
    if platform.system() == 'Linux':
        return is_window_open(title)
    else:
        # Use Selenium for cross-platform support
        return get_existing_browser_info(title=title, url=url)
def open_browser_with_devtools(url=None, title="My Permanent Tab", html_file_path=None, html_content=None, duplicate=False, fullscreen=False):
    """Open a browser tab with DevTools open."""
    return open_browser_tab(
        url=url,
        title=title,
        html_file_path=html_file_path,
        html_content=html_content,
        duplicate=duplicate,
        fullscreen=fullscreen,
        inspect=True
    )
##browser_js = get_browser_tab_and_index(url = 'https://chatgpt.com',title = "chatgpt")

