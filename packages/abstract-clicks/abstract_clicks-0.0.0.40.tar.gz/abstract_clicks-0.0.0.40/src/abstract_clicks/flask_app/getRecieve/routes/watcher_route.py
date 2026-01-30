import threading
from ..imports import *
watcher_bp,logger = get_bp('watcher_bp',__name__,
                         url_prefix=URL_PREFIX,
                         static_folder=STATIC_FOLDER)


@watcher_bp.route('/start', methods=['GET'])
def start():
    start_watchers()
    return "File watchers started"

@watcher_bp.route('/')
def index():
    return "File watcher Flask app running"


