import subprocess
import mms
import re
import time
import pyautogui

def manage_browser(browser_name="firefox", monitor_name="HDMI-1", url="https://example.com"):
    """
    Locate or open a browser, move it to a monitor, fullscreen it, navigate to a URL, and open inspect.
    
    Args:
        browser_name (str): Browser to use ("firefox" or "chrome").
        monitor_name (str): Target monitor name (e.g., "HDMI-1").
        url (str): URL to navigate to.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    def run_command(cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    # Step 1: Locate an open browser
    browser_patterns = {
        "firefox": "Mozilla Firefox",
        "chrome": "Google Chrome|Chromium"
    }
    if browser_name not in browser_patterns:
        print(f"Unsupported browser: {browser_name}")
        return False

    output = run_command("wmctrl -l -p")
    win_id = None
    for line in output.splitlines():
        if re.search(browser_patterns[browser_name], line):
            win_id = line.split()[0]
            break

    # Step 2: Open browser if not found
    if not win_id:
        browser_commands = {
            "firefox": "firefox",
            "chrome": "google-chrome"
        }
        run_command(f"{browser_commands[browser_name]} &")
        time.sleep(3)  # Wait for browser to open
        output = run_command("wmctrl -l -p")
        for line in output.splitlines():
            if re.search(browser_patterns[browser_name], line):
                win_id = line.split()[0]
                break
        if not win_id:
            print(f"Failed to open {browser_name}")
            return False

    # Step 3: Move to specified monitor
    monitors = []
    output = run_command("xrandr --query | grep ' connected'")
    for line in output.splitlines():
        match = re.match(r'(\S+)\s+connected\s+(\d+)x(\d+)\+(\d+)\+(\d+)', line)
        if match:
            name, width, height, x, y = match.groups()
            monitors.append((name, int(x), int(y)))
    
    target_monitor = None
    for name, x, y in monitors:
        if name == monitor_name:
            target_monitor = (x, y)
            break
    if not target_monitor:
        print(f"Monitor {monitor_name} not found")
        return False

    run_command(f"wmctrl -i -r {win_id} -e 0,{target_monitor[0]},{target_monitor[1]},-1,-1")

    # Step 4: Fullscreen
    run_command(f"wmctrl -i -r {win_id} -b add,maximized_vert,maximized_horz")
    run_command(f"xdotool windowactivate {win_id}")
    pyautogui.press("f11")  # Ensure fullscreen
    time.sleep(1)

    # Step 5: Navigate to URL
    run_command(f"xdotool windowactivate {win_id}")
    pyautogui.hotkey("ctrl", "t")  # New tab
    time.sleep(0.5)
    pyautogui.write(url)
    pyautogui.press("enter")
    time.sleep(1)

    # Step 6: Open inspect (developer tools)
    run_command(f"xdotool windowactivate {win_id}")
    if browser_name == "firefox":
        pyautogui.hotkey("ctrl", "shift", "i")
    elif browser_name == "chrome":
        pyautogui.hotkey("ctrl", "shift", "i")
    time.sleep(1)

    print(f"Successfully managed {browser_name} on {monitor_name} with URL {url}")
    return True

# Example usage
if __name__ == "__main__":
 with mss.mss() as sct:
    monitors = sct.monitors
    for monitor_index,monitor in enumerate(monitors):
        if monitor_index < 1 or monitor_index >= len(monitors):
            print(f"Invalid monitor index: {monitor_index}. Available monitors: {len(monitors)-1}")
            continue
        monitor = monitors[monitor_index]
        manage_browser(browser_name="firefox", monitor_name=monitor, url="https://example.com")

