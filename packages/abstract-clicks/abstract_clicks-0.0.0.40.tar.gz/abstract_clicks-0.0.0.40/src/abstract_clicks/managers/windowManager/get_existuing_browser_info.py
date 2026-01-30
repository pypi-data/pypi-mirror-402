import subprocess
import platform
import psutil
from abstract_webtools import get_soup
from abstract_utilities import write_to_file
import webbrowser
import time

def is_window_open(title):
    if isinstance(title, list):
        title = title[0]  # Extract first title if list
    if not title:
        print("No valid title provided")
        return {}
    
    if platform.system() == 'Linux':
        try:
            # Search for windows with partial title match
            result = subprocess.run(
                ['xdotool', 'search', '--name', title],
                capture_output=True, text=True
            )
            wids = [w for w in result.stdout.split() if w.strip()]
            if not wids:
                print(f"No window found with title: {title}")
                # Fallback: Try common browser names
                for fallback in ['Firefox', 'Chrome', 'Navigator']:
                    result = subprocess.run(
                        ['xdotool', 'search', '--name', fallback],
                        capture_output=True, text=True
                    )
                    wids = [w for w in result.stdout.split() if w.strip()]
                    if wids:
                        print(f"Fallback: Found window with title containing '{fallback}'")
                        break
                if not wids:
                    return {}

            # Get the newest window
            wid = wids[-1]
            real_title = subprocess.run(
                ['xdotool', 'getwindowname', wid],
                capture_output=True, text=True
            ).stdout.strip()
            pid = subprocess.run(
                ['xdotool', 'getwindowpid', wid],
                capture_output=True, text=True
            ).stdout.strip()

            # Validate PID
            if not pid.isdigit():
                print(f"Invalid PID for window {wid}: {pid}")
                return {}

            url = get_browser_url_from_pid(pid)
            info = {
                'window_id': wid,
                'title': real_title,
                'pid': pid,
                'url': url or 'Unknown'
            }
            print("Found window:", info)
            return info
        except subprocess.CalledProcessError as e:
            print(f"xdotool error: {e}")
            return {}
        except Exception as e:
            print(f"Error finding window: {e}")
            return {}
    else:
        print("Non-Linux system. Use Selenium or another tool.")
        return {}
def open_browser_tab(self, url=None, title="My Permanent Tab", html_file_path=None, html_content=None, duplicate=False):
    soup = call_soup(url=url)
    browser_title = get_title(soup=soup) or title
    info = is_window_open(browser_title)
    
    if info and not duplicate:
        return info
    
    html_content = get_html_content(html_content=html_content)
    html_file_path = html_file_path or self.html_file_path
    if html_content and html_file_path:
        write_to_file(contents=html_content, file_path=html_file_path)
    
    webbrowser.open_new_tab(url)
    
    # Retry finding the window
    for attempt in range(3):
        time.sleep(2.0)  # Increased delay
        info = is_window_open(browser_title)
        if info and info.get('window_id'):
            return info
        print(f"Attempt {attempt + 1}: No window found with title '{browser_title}'")
    
    print(f"Failed to open or find window for URL: {url}")
    return {'window_id': None, 'title': browser_title, 'pid': None}
def get_browser_url_from_pid(pid):
    """Attempt to infer the URL from a browser process (simplified)."""
    try:
        process = psutil.Process(int(pid))
        # This is a placeholder; actual URL extraction requires browser-specific APIs
        # For example, use Selenium or browser debugging protocols
        return None  # Replace with actual logic if available
    except psutil.NoSuchProcess:
        return None


