from ...imports import *
from ...utils import *
from ..monitorCapture import MonitorCaptureConfig
def if_none_get_default(data, default):
    if data is None:
        data =  default
    return data    
def move_to_target_item(target_item,left,top,duration=0.5):
    target_item = target_item
    x = target_item.get('x',0) + target_item.get('width',0) + left
    y = target_item.get('y',0) + target_item.get('height',0) + top
    get_auto_gui().moveTo(x,y, duration=0.5)
def get_target_items(
    target_text,
    target_text_lower,
    extracted_texts,
    extracted_texts_lower,
    top,
    left
    ):
    types = ['=','+','-']
    for typ in types:
        target_items = [item for
                             item in
                             extracted_texts_lower if
                             if_in_string(string=item.get('text_lower'),
                                          comp_string=target_text_lower,
                                          typ=typ)]
        if target_items:
            break
    for target_item in target_items:
        move_to_target_item(target_item,left,top,duration=duration)
class screenshotManager:
    def __init__(self, *args, **kwargs):
        config = get_inputs(MonitorCaptureConfig, *args, **kwargs)
        self.output_file = get_screenshot_file_path(config.output_file)
        self.target_text = config.target_text
        self.functions = config.functions
        self.target_image = config.target_image
        self.target_text_lower = [item.lower() for item in self.target_text]
        self.sct = mss.mss()  # Create the mss object here
        monitors = self.sct.monitors  # Now you can access monitors safely
        # Validate monitor index
        self.monitor_index = (
            int(config.monitor_index)
            if 1 <= int(config.monitor_index)< len(monitors)
            else 1
        )
        self.monitor = monitors[self.monitor_index]
        self.left = self.monitor['left'] or 0
        self.top = self.monitor['top'] or 0
        # Take the screenshot
        self.sct_img = self.sct.grab(self.monitor)
        self.size = self.sct_img.size
        self.rgb = self.sct_img.rgb
        self.img = Image.frombytes("RGB", self.size, self.rgb)
        self.extracted_texts = get_extracted_texts_and_coords(self.img)
        self.extracted_texts_lower = [lower_dict_string(item,'text') for item in self.extracted_texts]
        self.best_screenshot_result = get_best_screenshot_dict(
            screenshot_file = self.output_file,
            monitor_index = self.monitor_index,
            functions = self.functions,
            target_image = self.target_image,
            comp_obj=self.target_text)
    def save(self, path=None):
        path = path or self.output_file
        self.img.save(path)
        return path


    def get_target_items(
        self,
        target_text = None,
        target_text_lower = None,
        extracted_texts = None,
        extracted_texts_lower = None,
        top = None,
        left = None
        ):
        
        get_target_items(
            target_text = if_none_get_default(target_text,self.target_text),
            target_text_lower = if_none_get_default(target_text_lower,self.target_text_lower),
            extracted_texts = if_none_get_default(extracted_texts,self.extracted_texts),
            extracted_texts_lower = if_none_get_default(extracted_texts_lower,self.extracted_texts_lower),
            top = if_none_get_default(top,self.top),
            left = if_none_get_default(left,self.left),
            )
