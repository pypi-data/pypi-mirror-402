from imports import *
URL='https://example.com'
titlemanager = get_titlemanager()
window_mgr = WindowManager()
titlemanager.open_browser_tab(url=URL)
input(window_mgr.get_existing_browsers_data(url=URL,title='examp'))

