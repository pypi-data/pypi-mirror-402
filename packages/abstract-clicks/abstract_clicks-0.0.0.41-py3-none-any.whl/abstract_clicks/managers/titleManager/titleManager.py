from ...imports import *
from abstract_utilities import SingletonMeta
def assure_storage_path(file_path):
    if not os.path.isfile(file_path):
        safe_dump_to_file(data={},file_path=file_path)
    
class titleManager(metaclass=SingletonMeta):
    """Comprehensive title manager for browser windows."""
    def __init__(self, storage_path=None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.titles = {}  # {sudo_title: {url, title, browser_title, window_id, pid, html, soup, tab_index}}
            self.storage_path = storage_path or "title_manager_data.json"
            self.load_titles()

    def load_titles(self):
        """Load titles from storage file."""
        try:
            assure_storage_path(self.storage_path)
            if os.path.isfile(self.storage_path):
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
    
    def make_title(self, title=None, url=None, html_content=None, html_file_path=None,open_browser=True):
        """Create or update a title entry with associated metadata."""
        if not title and not url:
            print("Title or URL required")
            return False

        try:
            # Get browser title from URL
            browser_title = get_title(url=url) if url else title
            sudo_title = title or browser_title or str(uuid.uuid4())  # Fallback to UUID

            # Check if window exists
            info = self.find_tab(url=url, title=title, browser_title=browser_title)
            if open_browser:
                # Open new tab if no window found
                info = self.open_browser_tab(url=url, title=sudo_title, html_content=html_content, html_file_path=html_file_path)
                
            # Update title entry
            self.titles[sudo_title] = {
                "url": url or info.get("url", "Unknown"),
                "title": sudo_title,
                "browser_title": browser_title or info.get("title", ""),
                "window_id": info.get("window_id"),
                "pid": info.get("pid"),
                "html": info.get("html"),
                "soup": None,  # Avoid serializing soup
                "tab_index": info.get("tab_index")
            }
            self.save_titles()
            
            return self.titles[sudo_title]
        except Exception as e:
            print(f"Error making title: {e}")
            return False

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
def open_browser_with_devtools(url=None, title="My Permanent Tab", html_file_path=None, html_content=None, duplicate=False, fullscreen=False):
    """Open a browser tab with DevTools open."""
    return get_titlemanager().open_browser_tab(
        url=url,
        title=title,
        html_file_path=html_file_path,
        html_content=html_content,
        duplicate=duplicate,
        fullscreen=fullscreen,
        inspect=True
    )
