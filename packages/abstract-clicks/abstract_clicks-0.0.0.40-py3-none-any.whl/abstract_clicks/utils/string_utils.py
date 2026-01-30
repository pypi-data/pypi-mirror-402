from ..imports import *
from ..utils import *
from ..managers.shadow_functions import get_clipboard,get_ocr_locate_image
##from ..managers import get_auto_gui
from difflib import SequenceMatcher
clipboard = get_clipboard()
from difflib import SequenceMatcher
from typing import Any, Callable, Iterable, Optional
from abstract_utilities import make_list
def if_case_sensative(obj,case_sensative=False):
    if not case_sensative:
        obj = str(obj).lower()
    return obj
def get_closest_object_by_compartments(
    target_comps: list[str],
    candidates: Iterable[Any],
    key: Callable[[Any], str] = lambda o: str(o),
    split_func: Optional[Callable[[str], list[str]]] = None,
    case_sensative=False
) -> Optional[Any]:
    """
    • target_comps:      your list like ['this',' ','string']  
    • candidates:        any iterable of “comparable objects”  
    • key(obj) → str:    how to pull a single string out of each candidate  
    • split_func(s) → list[str]: 
         how to break *that* candidate‐string into its own compartments  
         (defaults to treating the entire string as one compartment)
    
    Returns the candidate object whose compartments best match your target_comps.
    """
    if split_func is None:
        # by default, candidate is one big compartment
        split_func = lambda s: [s]

    best_obj = None
    best_score = -1.0
    case_sensative = case_sensative or False
    # drop any empty target compartments
    targets = [if_case_sensative(t,case_sensative=case_sensative) for t in target_comps if t.strip()]
    if not targets:
        return None

    for obj in candidates:
        cand_str = key(obj)
        cand_comps = [if_case_sensative(c,case_sensative=case_sensative) for c in split_func(cand_str) if c.strip()]
        if not cand_comps:
            continue

        # for each target compartment, find its *best* match among candidate compartments
        per_target_scores = []
        for t in targets:
            scores = [SequenceMatcher(None, t, c).ratio() for c in cand_comps]
            per_target_scores.append(max(scores))

        # average across all your target compartments
        avg_score = sum(per_target_scores) / len(per_target_scores)

        if avg_score > best_score:
            best_score, best_obj = avg_score, obj

    return best_obj
def lower_dict_string(dict_obj,key):
    dict_obj[f"{key}_lower"] = str(dict_obj[key]).lower()
    return dict_obj
def if_in_string(string=None,comp_string=None,typ=None):
    typ = typ or '='
    if comp_string and string:
        if typ == '=':
            if string == comp_string:
                return True
        elif typ == '+':
             if comp_string in string:
                return True   
        elif typ == '-':
            if string in comp_string:
                return True    
    return False

def get_dict_coords(best_dict,monitor_info):
    if best_dict:
        best_dict = best_dict[0]
        x = best_dict['x'] + best_dict['width'] // 2
        y = best_dict['y'] + best_dict['height'] // 2
        # Adjust for monitor offset
        if monitor_info:
            x += monitor_info['left']
            y += monitor_info['top']
        # Move mouse
        get_auto_gui().moveTo(x, y, duration=0.5)  # Smooth movement over 0.5s
        return True
def get_image_closest_match(main_file_path=None,
                            images=None,
                            text=None,
                            dicts=None,
                            monitor_info=None,
                            functions=None):
    if images:
        functions= functions or []
        image_closest_match=None
       
        for template_file_path in images:
            image_closest_match = get_ocr_locate_image(main_file_path=main_file_path,
                                 template_file_path=template_file_path,
                                 text=text)
            result = get_dict_coords(image_closest_match,monitor_info)
            if result:
                for function in functions:
                    function(result)
            return result
def get_text_closest_match(screenshot_file,
                           comp_obj,
                           dicts,
                           monitor_info,
                           monitor_index,
                           functions):
        dicts = clipboard.perform_ocr(screenshot_file=screenshot_file,
                                      confidence_threshold=60)#clipboard.perform_ocr(file_path)
        texts = [text.get('text') for text in dicts]
        vars_js = {}
        for key in comp_obj:
      
            closest_match = get_closest_object_by_compartments(
                target_comps = comp_obj,
                candidates    = texts,
                key           = lambda s: s,
                split_func    = lambda s: s.split(),   # break each OCR text into words
                case_sensative=False
            )
            
   
            vars_js[key]=get_closest_match(dicts=dicts,closest_match=closest_match,monitor_info=monitor_info)
             
        return vars_js

def get_best_comprable(comp_obj,
                       total_list,
                       case_sensative=False):
    best = get_closest_match_from_list(comp_obj=comp_obj,
                                       total_list=total_list,
                                       case_sensative=case_sensative)
    return best
def get_closest_match(dicts=None,closest_match=None,monitor_info=None,functions=None):
    if dicts:
        functions= functions or []
        best_dict = [item for item in dicts if item.get('text') == closest_match]
        result = get_dict_coords(best_dict,monitor_info)
        for function in functions:
            function(result)
        return result
def get_best_screenshot_dict(screenshot_file='snapshot.png',
                             monitor_index=1,
                                  functions=None,
                                  target_image=None,
                                  comp_obj='html'):
    image_closest_match = screenshot_file
    text_closest_match = target_image
    
    monitor_index = monitor_index or 1
    comp_obj = make_list(comp_obj)
    monitor_info = clipboard.screenshot_specific_screen(screenshot_file,monitor_index)
    if monitor_info:
        dicts = clipboard.perform_ocr(screenshot_file=screenshot_file,
                                      confidence_threshold=60)#clipboard.perform_ocr(file_path)
        if target_image:
            image_closest_match = get_image_closest_match(main_file_path=screenshot_file,
                            images=target_image,
                            text=comp_obj,
                            functions=functions,
                            dicts=dicts,
                            monitor_info=monitor_info)
        else:
            text_closest_match = get_text_closest_match(
                screenshot_file,
                comp_obj=comp_obj,
                dicts=dicts,
                functions=functions,
                monitor_info=monitor_info,
                monitor_index=monitor_index)
        return image_closest_match or text_closest_match
           
            
     
