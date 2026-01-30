from abstract_clicks.imports import *
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
try:
    import win32gui
except ImportError:
    win32gui = None
try:
    from AppKit import NSWorkspace
    import objc
except ImportError:
    NSWorkspace = None

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

def is_window_open(url=None, title=None, browser_title=None):
    """Check if a window exists with the given title or browser title."""
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
                        'url': url
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
                    'pid': None,  # Requires additional logic
                    'url': url or 'Unknown'
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
                            'url': url or 'Unknown'
                        }
            print(f"No window found with titles: {titles}")
            return {}
        except Exception as e:
            print(f"Error finding window on macOS: {e}")
            return {}
    else:
        return get_existing_browser_info(title=titles[0] if titles else None, url=url)

def get_browser_url_from_pid(pid):
    """Placeholder for inferring URL from PID (requires browser-specific APIs)."""
    try:
        process = psutil.Process(int(pid))
        return None  # Implement with Chrome DevTools or similar
    except psutil.NoSuchProcess:
        return None

def get_existing_browser_info(title=None, url=None):
    """Use Selenium to find an existing browser window."""
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Could not connect to existing browser: {e}")
        driver = webdriver.Chrome()

    try:
        windows = driver.window_handles
        for window in windows:
            driver.switch_to.window(window)
            current_title = driver.title
            current_url = driver.current_url
            if (title and title.lower() in current_title.lower()) or (url and url in current_url):
                info = {
                    "window_id": window,
                    "title": current_title,
                    "url": current_url,
                    "html": driver.page_source,
                    "soup": BeautifulSoup(driver.page_source, 'html.parser')
                }
                return info
        print(f"No browser window found with title: {title} or URL: {url}")
        return {}
    except Exception as e:
        print(f"Error with Selenium: {e}")
        return {}
    finally:
        if driver:
            driver.quit()

class titleManager(metaclass=SingletonMeta):
    """Comprehensive title manager for browser windows."""
    def __init__(self, storage_path=None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.titles = {}  # {sudo_title: {url, title, browser_title, window_id, pid, html, soup}}
            self.storage_path = storage_path or "title_manager_data.json"
            self.load_titles()

    def load_titles(self):
        """Load titles from storage file."""
        try:
            if read_from_file(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.titles = {k: v for k, v in data.items() if isinstance(v, dict)}
        except Exception as e:
            print(f"Error loading titles: {e}")

    def save_titles(self):
        """Save titles to storage file."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.titles, f, indent=2)
        except Exception as e:
            print(f"Error saving titles: {e}")

    def make_title(self, title=None, url=None, html_content=None, html_file_path=None):
        """Create or update a title entry with associated metadata."""
        if not title and not url:
            print("Title or URL required")
            return False

        try:
            # Get browser title from URL
            browser_title = get_title(url=url) if url else title
            sudo_title = title or browser_title or str(uuid.uuid4())  # Fallback to UUID

            # Check if window exists
            info = is_window_open(url=url, title=title, browser_title=browser_title)
            if not info and url:
                # Open new tab if no window found
                info = self.open_browser_tab(url=url, title=sudo_title, html_content=html_content, html_file_path=html_file_path)

            # Update title entry
            self.titles[sudo_title] = {
                "url": url or info.get("url", "Unknown"),
                "title": sudo_title,
                "browser_title": browser_title,
                "window_id": info.get("window_id"),
                "pid": info.get("pid"),
                "html": info.get("html"),
                "soup": None  # Avoid serializing soup
            }
            self.save_titles()
            return self.titles[sudo_title]
        except Exception as e:
            print(f"Error making title: {e}")
            return False

    def get_window_info(self, url=None, title=None, browser_title=None):
        """Retrieve information about an existing window."""
        try:
            info = is_window_open(url=url, title=title, browser_title=browser_title)
            if info:
                sudo_title = title or browser_title or info.get("title")
                if sudo_title:
                    self.titles[sudo_title] = self.titles.get(sudo_title, {})
                    self.titles[sudo_title].update(info)
                    self.save_titles()
                return info
            return {}
        except Exception as e:
            print(f"Error getting window info: {e}")
            return {}

    def get_title_from_url(self, url):
        """Get the title for a given URL."""
        try:
            browser_title = get_title(url=url)
            if browser_title:
                self.titles[browser_title] = self.titles.get(browser_title, {})
                self.titles[browser_title].update({"url": url, "browser_title": browser_title})
                self.save_titles()
            return browser_title
        except Exception as e:
            print(f"Error getting title from URL: {e}")
            return ""

    def open_browser_tab(self, url=None, title="My Permanent Tab", html_file_path=None, html_content=None, duplicate=False):
        """Open a new browser tab or return existing window info."""
        try:
            soup = call_soup(url=url)
            browser_title = get_title(soup=soup)
            info = self.get_window_info(title=title, browser_title=browser_title, url=url)
            if info and not duplicate:
                return info

            html_content = get_html_content(html_content=html_content, title=title)
            if html_content and html_file_path:
                write_to_file(contents=html_content, file_path=html_file_path)
                url = url or f"file://{html_file_path}"

            webbrowser.open_new_tab(url)
            time.sleep(1.0)  # Wait for tab to open
            info = self.get_window_info(title=title, browser_title=browser_title, url=url)
            return info
        except Exception as e:
            print(f"Error opening browser tab: {e}")
            return {"window_id": None, "title": title, "pid": None, "url": url}

    def switch_window(self, title):
        """Switch focus to a window by title."""
        try:
            if platform.system() == 'Linux':
                result = subprocess.run(
                    ['xdotool', 'search', '--name', title],
                    capture_output=True, text=True
                )
                window_ids = result.stdout.strip().split()
                if window_ids:
                    subprocess.run(['xdotool', 'windowactivate', window_ids[0]])
                    print(f"Switched to window: {title}")
                    return True
                print(f"No window found: {title}")
                return False
            elif platform.system() == 'Windows' and win32gui:
                def callback(hwnd, target):
                    if title.lower() in win32gui.GetWindowText(hwnd).lower():
                        win32gui.SetForegroundWindow(hwnd)
                        return False
                win32gui.EnumWindows(callback, None)
                print(f"Switched to window: {title}")
                return True
            elif platform.system() == 'Darwin' and NSWorkspace:
                workspace = NSWorkspace.sharedWorkspace()
                for app in workspace.runningApplications():
                    if title.lower() in app.localizedName().lower():
                        app.activateWithOptions_(0)
                        print(f"Switched to window: {title}")
                        return True
                print(f"No window found: {title}")
                return False
            else:
                print("Unsupported platform for window switching")
                return False
        except Exception as e:
            print(f"Error switching window: {e}")
            return False

    def delete_title(self, title):
        """Remove a title entry."""
        try:
            if title in self.titles:
                del self.titles[title]
                self.save_titles()
                return True
            return False
        except Exception as e:
            print(f"Error deleting title: {e}")
            return False

    def get_all_titles(self):
        """Return all stored titles."""
        return self.titles

def make_title(title=None, url=None):
    """Convenience function to create a title."""
    title_mgr = titleManager()
    return title_mgr.make_title(title=title, url=url)
def get_titlemanager():
    titlemanager = titleManager()
    return titlemanager
titlemanager = get_titlemanager()
def load_titles():
        return titlemanager.load_titles()

def save_titles():
        return titlemanager.save_titles()

def make_title(title=None,url=None,html_content=None,html_file_path=None):
        return titlemanager.make_title(title=title,url=url,html_content=html_content,html_file_path=html_file_path)

def get_window_info(url=None,title=None,browser_title=None):
        return titlemanager.get_window_info(url=url,title=title,browser_title=browser_title)

def get_title_from_url(url):
        return titlemanager.get_title_from_url(url=url)

def open_browser_tab(url=None,title="My Permanent Tab",html_file_path=None,html_content=None,duplicate=False):
        return titlemanager.open_browser_tab(url=url,title=title,html_file_path=html_file_path,html_content=html_content,duplicate=duplicate)

def switch_window(title):
        return titlemanager.switch_window(title=title)

def callback(hwnd,target):
        return titlemanager.callback(hwnd=hwnd,target=target)

def delete_title(title):
        return titlemanager.delete_title(title=title)

def get_all_titles():
        return titlemanager.get_all_titles()
