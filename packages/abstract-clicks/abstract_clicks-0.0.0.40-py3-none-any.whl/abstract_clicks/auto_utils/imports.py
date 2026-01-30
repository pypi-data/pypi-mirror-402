from abstract_webtools import get_soup
from abstract_utilities import (SingletonMeta,
                                write_to_file,
                                read_from_file,
                                re,
                                os,
                                subprocess,
                                time,
                                json,
                                safe_load_from_json)
from typing import List, Dict, Optional, Union, Callable
from abstract_utilities.compare_utils import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pyautogui,subprocess,uuid,random,platform,platform,psutil,webbrowser
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
def update_dict_objs(dict_obj,up_dict_obj,title):
    if title and dict_obj.get(title) == None:
        dict_obj[title] = {}
    for key,values in up_dict_obj.items():
        if isinstance(values,list):
            curr_value = dict_obj[title].get(key)
            if curr_value is None:
                dict_obj[title][key]=[]
            for value in values:
                if value not in dict_obj[title][key]:
                    dict_obj[title][key].append(value)
        elif isinstance(values,dict):
            if key and dict_obj.get(key) == None:
                dict_obj[title][key] = {}
            dict_obj[title][key] = update_dict_objs(dict_obj[title],values,key)
        else:
            dict_obj[title][key]= value or dict_obj[title][key]
    return dict_obj
class titleManager(metaclass=SingletonMeta):
    """Comprehensive title manager for browser windows."""
    def __init__(self, storage_path=None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.titles = {}  # {sudo_title: {url, title, browser_title, window_id, pid, html, soup, tab_index}}
            self.storage_path = storage_path or "title_manager_data.json"
            self.load_titles()
            self._open_listeners: List[Callable[[Dict], None]] = []

    def add_open_listener(self, fn: Callable[[Dict], None]):
        self._open_listeners.append(fn)

    def _fire_open(self, info: Dict):
        for fn in self._open_listeners:
            try:
                fn(info)
            except Exception:
                pass
    def _rebuild_index(self):
        self.url_map = {
            info.get('url'): sudo
            for sudo, info in self.titles.items()
            if info.get('url')
        }
    def load_titles(self):
        """Load titles from storage file."""
      
        if not os.path.isfile(self.storage_path):
            safe_dump_to_file(data=self.titles,file_path=self.storage_path)
        self.titles =safe_load_from_json(file_path=self.storage_path)


    def save_titles(self):
        """Save titles to storage file."""
        try:
            safe_dump_to_file(data=self.titles,file_path=self.storage_path)
        except Exception as e:
            print(f"Error saving titles: {e}")
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
    def update_title(self,up_dict_obj:dict={},title=None):
        """Remove a title entry."""
        try:
            self.titles = update_dict_objs(self.titles,up_dict_obj,title)
            self.save_titles()
        except Exception as e:
            print(f"Error deleting title: {e}")
            return False
    def get_all_titles(self):
        """Return all stored titles."""
        return self.titles
    def make_title(self,
                   title: Optional[str]   = None,
                   url: Optional[str]     = None,
                   html_content: Optional[str] = None,
                   html_file_path: Optional[str]= None,
                   open_browser: bool     = True,
                   duplicate: bool        = False):
        """
        If duplicate==False and we already have a live tab for this URL or sudo-title,
        just return it; otherwise open a new one.
        """
        # 1) decide on the sudo_title (as you already do)
        browser_title = get_title(url=url) if url else title
        sudo_title   = title or browser_title or str(uuid.uuid4())

        # 2) look for an existing live tab
        info = self.find_tab(url=url, title=sudo_title, browser_title=browser_title)
        if info.get('window_id') and not duplicate:
            # we already have it; return the existing metadata
            return self.titles[sudo_title]

        # 3) otherwise, open a new tab (or file://)…
        if open_browser:
            info = WindowManager().open_browser_tab(
                url=url,
                title=sudo_title,
                html_file_path=html_file_path,
                html_content=html_content,
                duplicate=duplicate
            )

        # 4) now update our registry
        up = {
            "url":         url or info.get("url"),
            "title":       sudo_title,
            "browser_title": browser_title or info.get("title"),
            "window_id":   info.get("window_id"),
            "pid":         info.get("pid"),
            "html":        info.get("html"),
            "tab_index":   info.get("tab_index")
        }
        self.titles[sudo_title] = up
        self.save_titles()
        return up

    def get_sudo_for_url(self, url):
        return self.url_map.get(url)

    def get_url_for_sudo(self, sudo):
        return self.titles.get(sudo, {}).get("url")

    def find_tab(self, url=None, title=None, browser_title=None, window_id=None, pid=None):
        """Find a tab using multiple criteria."""
        try:
            # First, check cached titles
            for sudo_title, info in self.titles.items():
                if (url and url.lower() == info.get("url", "").lower()) or \
                   (title and title.lower() == info.get("title", "").lower()) or \
                   (browser_title and browser_title.lower() == info.get("browser_title", "").lower()) or \
                   (window_id and window_id == info.get("window_id")) or \
                   (pid and pid == info.get("pid")):
                    return info

            # Then, use Selenium for URL or title matching
            if url or title or browser_title:
                info = get_existing_browser_info(title=title or browser_title, url=url)
                if info:
                    return info

            # Finally, use platform-specific tools for title matching
            if title or browser_title:
                info = is_window_open(url=url, title=title, browser_title=browser_title)
                if info:
                    return info

            return {}
        except Exception as e:
            print(f"Error finding tab: {e}")
            return {}
    def open_browser_tab(self,
                         url=None,
                         title="My Permanent Tab",
                         html_file_path=None,
                         html_content=None,
                         open_browser=True,
                         duplicate=False):
        """Open a new browser tab or return existing window info."""
        try:
            soup = call_soup(url=url)
            browser_title = get_title(soup=soup)
            info = self.get_window_info(title=title, browser_title=browser_title, url=url)
            if info.get('window_id') and not duplicate:
                return info
        
            html_content = get_html_content(html_content=html_content, title=title)
            if html_content and html_file_path:
                write_to_file(contents=html_content, file_path=html_file_path)
                url = url or f"file://{html_file_path}"
            info = self.find_tab(url=url, title=title, browser_title=browser_title)

            # Only actually open when asked (and not a duplicate)
            if open_browser and not duplicate:
                webbrowser.open_new_tab(url)

                # ←— right after we open, grab final info…
                time.sleep(1.0)
                info = self.get_window_info(title=title, browser_title=browser_title, url=url)
                
                # Trigger the callback, if provided
                if on_open:
                    on_open(info)

                return info

            # if not opening, just return whatever info we had
            return info

        except Exception as e:
            print(f"Error opening browser tab: {e}")
            return {"window_id": None, "title": title, "pid": None, "url": url}
    def get_window_info(self, url=None, title=None, browser_title=None):
        """Retrieve information about an existing window."""
        try:
            info = self.find_tab(url=url, title=title, browser_title=browser_title)
            if info:
                sudo_title = title or browser_title or info.get("title") or str(uuid.uuid4())
                self.titles[sudo_title] = self.titles.get(sudo_title, {})
                self.titles[sudo_title].update(info)
                self.save_titles()
                return info
            return {}
        except Exception as e:
            print(f"Error getting window info: {e}")
            return {}

    def switch_window(self, title,*args,**kargs):
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
    # Wrapper functions for titleManager
def get_titlemanager():
    return titleManager()
tilemanager = get_titlemanager()


class WindowManager:
    # Command constants
    XRANDR_CMD = ['xrandr', '--query']
    WMCTRL_LIST_CMD = ['wmctrl', '-l', '-p']
    WMCTRL_MOVE_CMD = ['wmctrl', '-i', '-r']
    XDOTOOL_GEOMETRY_CMD = ['xdotool', 'getwindowgeometry']

    # Browser title signatures
    BROWSER_PATTERNS = [
        'Mozilla',
        'Firefox',
        'Google Chrome',
        'Chromium',
        'Microsoft Edge',
        'Opera',
        'Safari',
    ]

    # Regex patterns
    MONITOR_REGEX = re.compile(
        r'(\S+)\s+connected\s+(\d+)x(\d+)\+(\d+)\+(\d+)'
    )
    POSITION_REGEX = re.compile(r'Position:\s+(\d+),(\d+)')
    GEOMETRY_REGEX = re.compile(r'Geometry:\s+(\d+)x(\d+)')
    def __innit__(self):
        self.prior_titles = []
    @classmethod
    def get_monitors(cls) -> List[Dict[str, Union[str, int]]]:
        """Get monitor boundaries using xrandr."""
        monitors = []
        try:
            result = subprocess.run(
                cls.XRANDR_CMD,
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.splitlines():
                m = cls.MONITOR_REGEX.match(line)
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
        except FileNotFoundError:
            print("xrandr not installed or not found")
        except subprocess.SubprocessError as e:
            print(f"Error running xrandr: {e}")
        return monitors

    @classmethod
    def move_window_to_monitor(cls, window_id: str, monitor_name: str) -> bool:
        """
        Move a window to the specified monitor's top-left corner.
        """
        try:
            for mon in cls.get_monitors():
                if mon['name'] == monitor_name:
                    x, y = mon['x'], mon['y']
                    cmd = cls.WMCTRL_MOVE_CMD + [
                        window_id,
                        '-e', f"0,{x},{y},-1,-1"
                    ]
                    subprocess.run(cmd, check=True)
                    print(f"Moved window {window_id} to {monitor_name} ({x},{y})")
                    return True
            print(f"Monitor {monitor_name} not found")
            return False
        except FileNotFoundError as e:
            print(f"Required tool not found: {e}")
            return False
        except subprocess.SubprocessError as e:
            print(f"Error moving window: {e}")
            return False

    @classmethod
    def get_window_geometry(cls, window_id: str) -> Optional[Dict[str, int]]:
        """
        Get window position (x, y) and size (width, height) using xdotool.
        """
        try:
            result = subprocess.run(
                cls.XDOTOOL_GEOMETRY_CMD + [window_id],
                capture_output=True,
                text=True,
                check=True
            )
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            print(f"Error getting geometry: {e}")
            return None

        pos_m = cls.POSITION_REGEX.search(result.stdout)
        size_m = cls.GEOMETRY_REGEX.search(result.stdout)
        if pos_m and size_m:
            return {
                'x': int(pos_m.group(1)),
                'y': int(pos_m.group(2)),
                'width': int(size_m.group(1)),
                'height': int(size_m.group(2))
            }
        return None

    @classmethod
    def get_monitor_for_window(
        cls,
        window_id: Optional[str] = None,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Union[str, int]]:
        """
        Determine which monitor a given window (or coordinate) is on.
        Returns dict with monitor name, details, and window coords.
        """
        if window_id and (x is None or y is None):
            geom = cls.get_window_geometry(window_id)
            if not geom:
                return {}
            x, y = geom['x'], geom['y']

        if x is None or y is None:
            return {}

        for mon in cls.get_monitors():
            if mon['x'] <= x < mon['x'] + mon['width'] and \
               mon['y'] <= y < mon['y'] + mon['height']:
                return {
                    'monitor_name': mon['name'],
                    'monitor_details': f"{mon['width']}x{mon['height']}+{mon['x']}+{mon['y']}",
                    'win_x': x,
                    'win_y': y
                }
        return {}

    @classmethod
    def get_window_items(
        cls,
        windows: List[str],
        find_window_id: Optional[str] = None,
        find_desktop: Optional[str] = None,
        find_pid: Optional[str] = None,
        find_host: Optional[str] = None,
        find_window_title: Optional[str] = None
    ) -> Union[Dict[str, str], List[Dict[str, str]]]:
        """
        Parse `wmctrl -l -p` output lines into dicts, optionally filtering.
        """
        filters = {
            'window_id': find_window_id,
            'desktop': find_desktop,
            'pid': find_pid,
            'host': find_host,
            'window_title': find_window_title
        }
        # Remove None filters
        filters = {k: v for k, v in filters.items() if v is not None}

        parsed = []
        for line in windows:
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            win_id, desktop, pid, host, title = parts
            info = {
                'window_id': win_id,
                'desktop': desktop,
                'pid': pid,
                'host': host,
                'window_title': title
            }
            # Track monitor location as side effect if needed
            cls.get_monitor_for_window(window_id=win_id)

            parsed.append(info)
            if filters and all(info[k] == v for k, v in filters.items()):
                return info

        return parsed

    @classmethod
    def get_existing_browsers_data(
        cls,
        title: Optional[str] = None,
        url: Optional[str] = None,  # not yet used
        browser_title: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Find all browser windows using wmctrl. 
        If `title` is given, filters to closest matches.
        """
        try:
            result = subprocess.run(
                cls.WMCTRL_LIST_CMD,
                capture_output=True,
                text=True,
                check=True
            )
            windows = result.stdout.splitlines()
        except FileNotFoundError:
            print("wmctrl not installed or not found")
            return []
        except subprocess.SubprocessError as e:
            print(f"Error running wmctrl: {e}")
            return []

        # Parse all windows
        all_items = cls.get_window_items(windows)

        # Filter by browser-signatures
        browser_titles = [
            info['window_title']
            for info in (all_items if isinstance(all_items, list) else [all_items])
            if any(pat.lower() in info['window_title'].lower() for pat in cls.BROWSER_PATTERNS)
        ]
        browser_titles = make_list(browser_titles)
        # Optionally match closest titles
        if title and browser_titles:
            #from difflib import get_close_matches
            
            browser_titles = get_closest_match_from_list(title, total_list=browser_titles)
            browser_titles = make_list(browser_titles)
        self.prior_titles = browser_titles
            #browser_titles = get_close_matches(title, browser_titles, n=3)

        # Return full items for each matching title
        matched = [
            cls.get_window_items(windows, find_window_title=bt)
            for bt in browser_titles
        ]
        return matched
    

def logger(info):
    print("Opened:", info)

tilemanager = get_titlemanager()
tilemanager.add_open_listener(logger)
tilemanager.open_browser_tab(url="https://chatgpt.com")
