from ...imports import *
from .utils import *
import cv2
import os
import time
import platform
import threading
import subprocess
import pyperclip
import pyautogui
import mss
from PIL import Image
import pytesseract

import subprocess

def paste_modifier():
    try:
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
        print("Triggered external paste with xdotool")
    except Exception as e:
        print(f"xdotool paste failed: {e}")

def paste_modifier():
    subprocess.run(["xdotool", "key", "ctrl+v"])


from pynput import keyboard



# Assuming your SingletonMeta is already defined
class ClipboardManager(metaclass=SingletonMeta):
    def __init__(self):
        self.html_file_path = "/tmp/permanent_tab.html"
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.last_program_copy = None
            self.monitor_thread = None
            self.running = False
            self.clip = pyperclip
            # Define HTML file path
    # ------------------------------
    # COPY / PASTE
    # ------------------------------
    def custom_copy(self, text):
        """Wrap pyperclip.copy to track program-initiated copies."""
        pyperclip.copy(text)
        self.last_program_copy = text
        print(f"Program copied: {text}")

    def paste_modifier(self):
        """Trigger an actual external paste event."""
        system = platform.system()
        print('paste')
        try:
            if system == "Linux":
                # Prefer xdotool if available
                if shutil.which("xdotool"):
                    subprocess.run(["xdotool", "key", "ctrl+v"])
                else:
                    pyautogui.hotkey("ctrl", "v")
            elif system == "Darwin":  # macOS
                pyautogui.hotkey("command", "v")
            else:  # Windows
                pyautogui.hotkey("ctrl", "v")
            time.sleep(0.2)
        except Exception as e:
            print(f"Error simulating paste: {e}")
    def paste_to_file(file_path, clip):
        """Write current clipboard contents to a file after paste."""
        try:
            text = clip.paste()
            with open(file_path, 'w') as f:
                f.write(text)
            print(f"Pasted content saved to {file_path}")
        except Exception as e:
            print(f"Error saving pasted content: {e}")
    def paste_to_file(self, file_path):
        """Save current clipboard contents to a file."""
        try:
            text = self.clip.paste()
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(text)
            print(f"Pasted content saved to {file_path}")
        except Exception as e:
            print(f"Error saving pasted content: {e}")

    def custom_paste(self, file_path=None):
        """Perform a real paste event and log contents."""
        file_path = file_path or "/home/computron/Documents/cheatgpt/outputs/output.html"
        self.paste_modifier()
        print("Triggered paste into active window")
        self.paste_to_file(file_path)

    def screenshot_specific_screen(self,
                                   output_file="new_screen.png",
                                   monitor_index=1):
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
    def switch_window(self, window_title="My Permanent Tab"):
            """Switch to a window by partial title match (Linux with xdotool)."""
            if platform.system() != 'Linux':
                modifier = 'command' if platform.system() == 'Darwin' else 'alt'
                try:
                    get_auto_gui().keyDown(modifier)
                    time.sleep(0.1)
                    get_auto_gui().press('tab')
                    time.sleep(0.1)
                    get_auto_gui().keyUp(modifier)
                    print("Switched to first window (non-Linux fallback)")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error switching window: {e}")
                return
            try:
                time.sleep(1)
                result = subprocess.run(
                    ['xdotool', 'search', '--name', ''],
                    capture_output=True, text=True
                )
                window_ids = result.stdout.strip().split()
                print("Available window IDs:", window_ids)
                for wid in window_ids:
                    title = subprocess.run(
                        ['xdotool', 'getwindowname', wid],
                        capture_output=True, text=True
                    ).stdout.strip()
                    #print(f"Window ID {wid}: {title}")
                    if window_title.lower() in title.lower():
                        # Move to monitor 1 (adjust coordinates based on xrandr)
                        monitor_x, monitor_y = 1920, 0  # Example
                        subprocess.run(['xdotool', 'windowmove', wid, str(monitor_x), '0'])
                        subprocess.run(['xdotool', 'windowactivate', wid])
                        print(f"Switched and moved window to monitor {wid}: {window_title}")
                        time.sleep(0.5)
                        return wid
                print(f"No window found with title containing: {window_title}")
            except Exception as e:
                print(f"Error switching window with xdotool: {e}")

    
    def open_browser_tab(self, url=None, title="My Permanent Tab"):
            html_content = f"""
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
            try:
                with open(self.html_file_path, 'w') as f:
                    f.write(html_content)
                print(f"Saved HTML file: {self.html_file_path}")
            except Exception as e:
                print(f"Error saving HTML file: {e}")
                raise
            try:
                success = webbrowser.open(url)
                print(f"Opened browser tab with title: {title}, success: {success}")
            except Exception as e:
                print(f"Error opening browser: {e}")
                raise
    def get_extracted_texts_and_coords(self,img, confidence_threshold=None,objectType=None):
        
        confidence_threshold = confidence_threshold or 60
        extracted_texts=[]
        objectType = objectType or 'DICT'
        output_type = getattr(pytesseract.Output,objectType)
        data = pytesseract.image_to_data(img, output_type=output_type)
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > confidence_threshold:
                text = data['text'][i]
                if text.strip():
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    #print(f"Text: '{text}', X: {x}, Y: {y}, Width: {w}, Height: {h}")
                    extracted_texts.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'confidence': data['conf'][i]
                    })
        return extracted_texts
    
    def ocr_locate_image(self,main_file_path,template_file_path,text=None):
        # Load the main image and the template image
        print(f"main_file_path == {main_file_path}")
        print(f"template_file_path == {template_file_path}")
        main_image = cv2.imread(main_file_path, cv2.IMREAD_COLOR)
        template = cv2.imread(template_file_path, cv2.IMREAD_COLOR)
        # Check if images are loaded
        if main_image is None or template is None:
            raise ValueError(f"One or both images failed to load. main_image = {main_image} && template == {template}")
        # Get the dimensions of the template
        # Get the dimensions of the template
        h, w = template.shape[:2]
        # Perform template matching
        result = cv2.matchTemplate(main_image, template, cv2.TM_CCOEFF_NORMED)
        # Find the location with the highest match
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # Top-left corner of the matched region
        top_left = max_loc
        # Bottom-right corner
        bottom_right = (top_left[0] + w, top_left[1] + h)
        # Optional: Center coordinates
        x = top_left[0] + w // 2
        y = top_left[1] + h // 2
        
        center = [{
            'text':text,
            'image': template_file_path,
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'center':(x, y),
            'confidence': 100
        }]
        return center

    # ------------------------------
    # CLIPBOARD MONITORING
    # ------------------------------
    def monitor_clipboard(self, interval=0.5):
        """Monitor clipboard, ignoring program's own copies."""
        last_content = self.clip.paste()
        while self.running:
            try:
                current_content = self.clip.paste()
                if current_content != last_content and current_content != self.last_program_copy:
                    print("External clipboard change detected:", current_content)
                    last_content = current_content
                time.sleep(interval)
            except Exception as e:
                print(f"Error accessing clipboard: {e}")
                time.sleep(interval)


    def start_monitoring(self):
        """Start clipboard monitoring in a separate thread."""
        if not self.monitor_thread:
            self.running = True
            self.monitor_thread = threading.Thread(target=self.monitor_clipboard, daemon=True)
            self.monitor_thread.start()
            print("Started clipboard monitoring...")

    def stop_monitoring(self):
        """Stop clipboard monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
            self.monitor_thread = None
        print("Stopped clipboard monitoring.")

    def screenshot_specific_screen(self,
                                   output_file="new_screen.png",
                                   monitor_index=1):
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

    def perform_ocr(self,
                    screenshot_file="new_screen.png",
                    confidence_threshold=60):
        """Perform OCR on a screenshot and return extracted text with coordinates."""
        self.extracted_texts = perform_ocr(screenshot_file=screenshot_file,
                                           confidence_threshold=confidence_threshold)
        return self.extracted_texts
    def move_mouse_to_text(self,
                           extracted_texts,
                           monitor_info,
                           text_index=0,
                           target_text=None):
        """Move the mouse to the center of a text box from OCR results."""
        bool_response = move_mouse_to_text(extracted_texts=extracted_texts,
                       monitor_info=monitor_info,
                       text_index=text_index,
                       target_text=target_text)
        return nbool_response


    def screenshot_specific_screen(self,
                                   output_file="new_screen.png",
                                   monitor_index=1):
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

    def perform_ocr(self,
                    screenshot_file="new_screen.png",
                    confidence_threshold=60):
        """Perform OCR on a screenshot and return extracted text with coordinates."""
        self.extracted_texts = perform_ocr(screenshot_file=screenshot_file,
                                           confidence_threshold=confidence_threshold)
        return self.extracted_texts
    def move_mouse_to_text(self,
                           extracted_texts,
                           monitor_info,
                           text_index=0,
                           target_text=None):
        """Move the mouse to the center of a text box from OCR results."""
        bool_response = move_mouse_to_text(extracted_texts=extracted_texts,
                       monitor_info=monitor_info,
                       text_index=text_index,
                       target_text=target_text)
        return nbool_response
