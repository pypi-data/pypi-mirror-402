import webbrowser
def test_browser_open(url="https://chatgpt.com"):
    try:

        webbrowser.open(url)
        print(f"Opened browser with title: {driver.title}")
       
        return True
    except Exception as e:
        print(f"Failed to open browser: {e}")
        return False
#monitors = get_monitors()
#for monitor_index,monitor in  enumerate(monitors):
test_browser_open()
AUTO_DICTS = {
    "prompt":
    {
        "text":
        [
            'ask',
            ' ',
            'anything'],
        "image":
        [
            ],
        "functions":
        {
            "pre_functions":
            [
                ],
               "post_functions":
            [
                get_paste_in_prompt
                ]
            }
        },
    "enter":
    {
        "text":
        [
            ],
        "image":
        [
            "/home/computron/Pictures/Screenshots/Screenshot from 2025-06-09 06-37-25.png"
            ],
        "functions":
        {
            "pre_functions":
            [
                ],
               "post_functions":
            [
                get_html_inspect
                ]
            }
        },

    "inspect":
    {
        "text":
        [
            'ask',
            ' ',
            'anything'
            ],
        "image":
        [
            ],
        "functions":
        {
            "pre_functions":
            [
                ],

            "post_functions":
            [
                get_html_inspect
                ]
        }
    }
}

def get_example_browser():
    browser_js = get_browser_tab_and_index(url='https://example.com',
                          title="examplepage")
    return browser_js
def get_gpt_browser():
    browser_js = get_browser_tab_and_index(url='https://chatgpt.com',
                          title="chatgpt")

    return browser_js
def get_all_pointer_functions():
    for key,auto_dict in auto_dicts.items():
        get_pointer_function(key=key)
def get_pointer_function(key=None,
                         text=None,
                         image=None,
                         functions=None,
                         index=None,
                         output_file=None):
    auto_dict = AUTO_DICTS.get(key)
    if auto_dict:
        text = auto_dict.get('text',[])
        target_image = auto_dict.get('image',[])
        functions = auto_dict.get('functions',[])
    target_text = text or []
    target_image = target_image or []
    functions = functions or []
    monitor_index = index or 1
    output_file = output_file or 'snapshot.png'
    scnShtMgr = screenshotManager(output_file=output_file,
                                  monitor_index=monitor_index,
                                  functions=functions,
                                  target_image=target_image,
                                  target_text=target_text)

existing_browsers_info = [{'window_id': '0x15800e73',
                           'desktop': '-1',
                           'pid': '1171528',
                           'host': 'computron-System-Product-Name',
                           'window_title': 'Example Domain — Mozilla Firefox'},
                          {'window_id': '0x15800e73', 'desktop': '-1', 'pid': '1171528', 'host': 'computron-System-Product-Name',
                           'window_title': 'Example Domain — Mozilla Firefox'},
                          {'window_id': '0x10c00024', 'desktop': '0', 'pid': '543239', 'host': 'computron-System-Product-Name', 'window_title': 'nosee4u.ods — LibreOffice Calc'}, {'window_id': '0x15800e73', 'desktop': '-1', 'pid': '1171528', 'host': 'computron-System-Product-Name', 'window_title': 'Example Domain — Mozilla Firefox'}, {'window_id': '0x10c00024', 'desktop': '0', 'pid': '543239', 'host': 'computron-System-Product-Name', 'window_title': 'nosee4u.ods — LibreOffice Calc'}, {'window_id': '0x0e60005e', 'desktop': '-1', 'pid': '481167', 'host': 'computron-System-Product-Name', 'window_title': 'ubujew (Snapshot 1) [Running] - Oracle VM VirtualBox : 1'}, {'window_id': '0x098001f0', 'desktop': '0', 'pid': '0', 'host': 'N/A', 'window_title': 'compare_utils.py - /home/computron/miniconda/lib/python3.12/site-packages/abstract_utilities/compare_utils.py (3.12.4)'}]#get_existing_browsers_info()
def get_browserfor():
    
    window_id=existing_browser_info.get("window_id")
    geometry = get_window_geometry(window_id)
    monitors = get_monitors()
    existing_browser_info.update(get_monitor_location(window_id=window_id))
    existing_browser_info['window'] = get_window_geometry(window_id)
    control_browser_window(window_id=window_id,action="maximize")
    browser_name=existing_browser_info.get("window_title")
    open_new_tab_in_browser(url='https://example.com',
                            title=browser_name,
                            window_id=window_id)
    move_browser_to_monitor(window_id,
                            monitors[1])
    existing_browser_info.update(get_monitor_location(window_id=window_id))
    existing_browser_info['window'] = get_window_geometry(window_id)
    randomize_pointer_in_browser_area(window_id, area_offsets=None,
                                      half='right')
    pyautogui.click(button='right')
    pyautogui.hotkey('ctrl',
                     'shift',
                     'q')
    get_pointer_function(key="inspect",
                         index=1)
    
get_browserfor()
    

