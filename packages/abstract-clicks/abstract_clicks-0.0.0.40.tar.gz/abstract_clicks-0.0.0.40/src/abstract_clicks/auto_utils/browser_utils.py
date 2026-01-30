
def split_browser_area_vertically(window_id, area_offsets=None):
    """
    Split a browser window vertically into two equal halves and return their boundaries.
    
    Args:
        window_id (str): Window ID from get_window_items or get_existing_browsers_info.
        area_offsets (dict, optional): Offsets to define the area within the window.
            Example: {'top': 100, 'bottom': 50, 'left': 50, 'right': 50} (in pixels).
            Defaults to 10% margins on all sides.
    
    Returns:
        dict: Boundaries for each half, e.g., {'left': {'x_min': int, 'x_max': int, 'y_min': int, 'y_max': int}, 'right': {...}}.
              Returns None if geometry is unavailable or area is invalid.
    """
    try:
        # Get window geometry
        geometry = get_window_geometry(window_id)
        if not geometry:
            print(f"Could not get geometry for window {window_id}")
            return None

        win_x, win_y = geometry['x'], geometry['y']
        win_width, win_height = geometry['width'], geometry['height']

        # Define default area (10% margin on all sides)
        if area_offsets is None:
            area_offsets = {
                'top': int(win_height * 0.1),
                'bottom': int(win_height * 0.1),
                'left': int(win_width * 0.1),
                'right': int(win_width * 0.1)
            }

        # Calculate base area boundaries
        area_x_min = win_x + area_offsets.get('left', 0)
        area_x_max = win_x + win_width - area_offsets.get('right', 0)
        area_y_min = win_y + area_offsets.get('top', 0)
        area_y_max = win_y + win_height - area_offsets.get('bottom', 0)

        # Validate area
        if area_x_min >= area_x_max or area_y_min >= area_y_max:
            print("Invalid area dimensions after applying offsets")
            return None

        # Split area vertically
        area_width = area_x_max - area_x_min
        half_width = area_width // 2
        left_x_max = area_x_min + half_width
        right_x_min = left_x_max

        return {
            'left': {
                'x_min': area_x_min,
                'x_max': left_x_max,
                'y_min': area_y_min,
                'y_max': area_y_max
            },
            'right': {
                'x_min': right_x_min,
                'x_max': area_x_max,
                'y_min': area_y_min,
                'y_max': area_y_max
            }
        }

    except Exception as e:
        print(f"Error splitting browser area: {e}")
        return None
def randomize_pointer_in_browser_area(window_id, area_offsets=None, half=None):
    """
    Move the mouse pointer to a random position within the browser window.
    """
    try:
        geometry = get_window_geometry(window_id)
        if not geometry:
            print(f"Could not get geometry for window {window_id}")
            return False

        win_x, win_y = geometry['x'], geometry['y']
        win_width, win_height = geometry['width'], geometry['height']

        if area_offsets is None:
            area_offsets = {
                'top': int(win_height * 0.1),
                'bottom': int(win_height * 0.1),
                'left': int(win_width * 0.1),
                'right': int(win_width * 0.1)
            }

        if half in ['left', 'right']:
            boundaries = split_browser_area_vertically(window_id, area_offsets)
            if not boundaries:
                print(f"Could not split area for window {window_id}")
                return False
            area = boundaries[half]
            area_x_min, area_x_max = area['x_min'], area['x_max']
            area_y_min, area_y_max = area['y_min'], area['y_max']
        else:
            area_x_min = win_x + area_offsets.get('left', 0)
            area_x_max = win_x + win_width - area_offsets.get('right', 0)
            area_y_min = win_y + area_offsets.get('top', 0)
            area_y_max = win_y + win_height - area_offsets.get('bottom', 0)

        if area_x_min >= area_x_max or area_y_min >= area_y_max:
            print("Invalid area dimensions after applying offsets")
            return False

        rand_x = random.randint(area_x_min, area_x_max)
        rand_y = random.randint(area_y_min, area_y_max)

        subprocess.run(['xdotool', 'windowactivate', window_id], check=True)
        subprocess.run(['xdotool', 'mousemove', str(rand_x), str(rand_y)], check=True)
        print(f"Moved pointer to ({rand_x}, {rand_y}) in window {window_id} ({half if half else 'full'} area)")
        return True

    except FileNotFoundError as e:
        print(f"Required tool not found: {e}")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error moving pointer: {e}")
        return False
def get_monitors():
    """Get monitor boundaries using xrandr."""
    monitors = []
    try:
        result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            match = re.match(r'(\S+)\s+connected\s+(\d+)x(\d+)\+(\d+)\+(\d+)', line)
            if match:
                name, width, height, x_offset, y_offset = match.groups()
                monitors.append({
                    'name': name,
                    'x': int(x_offset),
                    'y': int(y_offset),
                    'width': int(width),
                    'height': int(height)
                })
    except FileNotFoundError:
        print("xrandr not installed or not found")
    except subprocess.SubprocessError as e:
        print(f"Error running xrandr: {e}")
    return monitors

def move_browser_to_monitor(window_id, monitor_name):
    """
    Move a browser window to the specified monitor.
    
    Args:
        window_id (str): Window ID from get_existing_browsers_info.
        monitor_name (str): Monitor name (e.g., 'HDMI-1').
    """
    try:
        monitors = get_monitors()
        for monitor in monitors:
            if monitor['name'] == monitor_name:
                # Move window to monitor's top-left corner
                subprocess.run([
                    'wmctrl', '-i', '-r', window_id,
                    '-e', f"0,{monitor['x']},{monitor['y']},-1,-1"
                ], check=True)
                print(f"Moved window {window_id} to monitor {monitor_name} ({monitor['x']},{monitor['y']})")
                return True
        print(f"Monitor {monitor_name} not found")
        return False

    except FileNotFoundError as e:
        print(f"Required tool not found: {e}")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error moving window: {e}")
        return False
def get_window_geometry(window_id):
    """Get window position (x, y) and size (width, height) using xdotool."""
   
    result = subprocess.run(['xdotool', 'getwindowgeometry', window_id], capture_output=True, text=True, check=True)
    # Example output: "Position: 100,200 (screen: 0)\nGeometry: 1280x720"
    pos_match = re.search(r'Position:\s+(\d+),(\d+)', result.stdout)
    size_match = re.search(r'Geometry:\s+(\d+)x(\d+)', result.stdout)

    if pos_match and size_match:
        return {
            'x': int(pos_match.group(1)),
            'y': int(pos_match.group(2)),
            'width': int(size_match.group(1)),
            'height': int(size_match.group(2))
        }
    return None

def get_position(window_id):
    position = get_window_geometry(window_id)
    #print(f"window_id == {window_id}")
    #print(f"position == {position}")
    if not position:
        return None,None
    win_x, win_y = position['x'],position['y']
    return win_x, win_y
def get_monitor_location(window_id=None,win_x=None, win_y=None):
    monitor_name = "Unknown"
    monitor_details = ""
    if None in [win_x,win_y]:
        win_x, win_y = get_position(window_id)
        if None in [win_x, win_y]:
            return {}
    for monitor in get_monitors():
        mx, my, mw, mh = monitor['x'], monitor['y'], monitor['width'], monitor['height']
        if (mx <= win_x < mx + mw) and (my <= win_y < my + mh):
            return {"monitor_name":monitor['name'],"monitor_details":f"{mw}x{mh}+{mx}+{my}","win_x":win_x,"win_y":win_y}
            break
    return {}
def get_window_items(windows,find_window_id=None, find_desktop=None, find_pid=None, find_host=None, find_window_title=None):
  find_js = {"window_id":find_window_id,"desktop":find_desktop,"pid":find_pid,"host":find_host,"window_title":find_window_title}
  find_js_items = find_js.copy()
  for key,value in find_js_items.items():
      if value == None:
          del find_js[key]
  all_parts = []
  for line in windows:
    
    # wmctrl -l -p format: <window_id> <desktop> <pid> <host> <title>
    parts = line.split(None, 4)
    if len(parts) < 5:
        continue
    window_id, desktop, pid, host, window_title = parts
    get_monitor_location(window_id=window_id)
    find_parts_js = {"window_id":window_id,"desktop":desktop,"pid":pid,"host":host,"window_title":window_title}
   
    breakit=True
    all_parts.append(find_parts_js)
    if find_js:
        for key,value in find_js.items():
            if find_parts_js.get(key) != value:
                breakit=False
                break
        if breakit != False:
            return find_parts_js
    
  return all_parts
def get_existing_browsers_data(title=None, url=None):
    """
    Find all browser windows on Linux using wmctrl and return their details.
    If title is provided, filter for matching windows; otherwise, return all browser windows.
    """
    
    try:
        # Run wmctrl to list windows with PIDs
        result = subprocess.run(['wmctrl', '-l', '-p'], capture_output=True, text=True, check=True)
        windows = result.stdout.splitlines()
        
        # Common browser signatures in titles (customize as needed)
        browser_patterns = [
            'Mozilla',
            'Firefox',
            'Google Chrome',
            'Chromium',
            'Microsoft Edge',
            'Opera',
            'Safari'  # Less common on Linux
        ]
        
        # Collect browser window info
        all_browsers = []
        all_parts = get_window_items(windows)
        for pattern in browser_patterns:
            for all_part in all_parts:
                if pattern.lower() in all_part.get('window_title').lower():
                    all_browsers.append(all_part.get('window_title'))
        
        # Check if it's a browser window
        if all_browsers:
            all_browsers = get_closest_match_from_list(title, total_list=all_browsers)
            browser_windows = [get_window_items(windows,find_window_title=browser) for browser in all_browsers]
            input(browser_windows)

            return browser_windows

    except FileNotFoundError:
        print("wmctrl not installed or not found")
        return []
    except subprocess.SubprocessError as e:
        print(f"Error running wmctrl: {e}")
        return []
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

def open_browser_tab(url=None, title="My Permanent Tab", html_file_path=None, html_content=None, duplicate=False, fullscreen=False, inspect=False):
    """Open a new browser tab or return existing window info, with optional full screen and inspect."""
    tilemanager = get_titlemanager()
    try:
        soup = call_soup(url=url)
        browser_title = get_title(soup=soup)
        info = tilemanager.find_tab(url=url, title=title, browser_title=browser_title)
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

def open_new_tab_in_browser(window_id, url=None, title=None):
    """
    Open a new tab in the specified browser window.
    
    Args:
        window_id (str): Window ID from get_existing_browsers_info (e.g., '0x01234567').
        url (str, optional): URL to open in the new tab.
        browser_name (str, optional): Browser type (e.g., 'Firefox', 'Google Chrome') to determine command.
    """
    try:
        browser_mappings = {
                    'firefox': 'Firefox',
                    'chrome': 'Google Chrome',
                    'chromium': 'Google Chrome',  # Treat Chromium as Chrome
                    'edge': 'Microsoft Edge',
                    'opera': 'Opera',
                    'safari': 'Safari'  # Less common on Linux
                }
        browser_name = title
        for key in list(browser_mappings.keys()):
            if key.lower() in title.lower():
                browser_value = browser_mappings.get(key)
                if browser_value.lower() in title.lower():
                    browser_name = browser_value
                    break
        # Activate the target window
        subprocess.run(['xdotool', 'windowactivate', window_id], check=True)


        # Build command to open new tab
        if browser_name == 'Firefox':
            cmd = ['firefox', '--new-tab']
            if url:
                cmd.append(url)
        elif browser_name == 'Google Chrome':
            cmd = ['google-chrome', '--new-tab']
            if url:
                cmd.append(url)
        elif browser_name == 'Microsoft Edge':
            cmd = ['microsoft-edge', '--new-tab']
            if url:
                cmd.append(url)
        else:
            print(f"Unsupported browser: {browser_name}")
            return False
        
        # Run command
        subprocess.run(cmd, check=True)
        print(f"Opened new tab in {browser_name} (window ID: {window_id})" + (f" with URL: {url}" if url else ""))
        return True

    except FileNotFoundError as e:
        print(f"Required tool not found: {e}")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error opening new tab: {e}")
        return False

def get_browser_tab_and_index(url=None, title=None):
        """Get tab info and index using comprehensive matching."""

       
             
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


def get_browser_url_from_pid(pid):
    """Placeholder for inferring URL from PID."""
    try:
        process = psutil.Process(int(pid))
        return None  # Implement with Chrome DevTools if needed
    except psutil.NoSuchProcess:
        return None

def get_browser_coordinates(url=None, title=None, browser_title=None, window_id=None):
    """Get the coordinates of a browser window."""
    
    return titlemanager.get_window_coordinates(url=url, title=title, browser_title=browser_title, window_id=window_id)


##browser_js = get_browser_tab_and_index(url = 'https://chatgpt.com',title = "chatgpt")


