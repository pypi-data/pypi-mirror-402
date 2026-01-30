from ..imports import read_from_file,pyperclip,time,get_abs_dir,get_query_path,get_response_path
from ..managers.changeHandler import ChangeHandler
from watchdog.observers import Observer

query_file_path = get_query_path()
response_file_path = get_response_path()
def my_query(path=None):
    query = read_from_file(query_file_path)
    pyperclip.copy(query)

def my_response(path=None):
    response = read_from_file(response_file_path)
    pyperclip.copy(response)

def get_files(dirname=None):
    file_paths = [os.path.join(dirname,item) for item in items if item]
    if file_paths:
        return ','.join(file_paths)
    return ''
def my_query_filewatch():
    handler = ChangeHandler(query_file_path,
                            my_query)
    observer = Observer()
    observer.schedule(handler,
                      path=path_to_watch.rsplit("/", 1)[0] or ".",
                      recursive=False)
    observer.start()
    print(f"Watching {prompt_file_path} for changes…")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def my_response_filewatch():
    handler = ChangeHandler(response_file_path,
                            my_response)
    observer = Observer()
    observer.schedule(handler,
                      path=path_to_watch.rsplit("/", 1)[0] or ".",
                      recursive=False)
    observer.start()
    print(f"Watching {prompt_file_path} for changes…")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()    
def run_watchers():
    query_thread = threading.Thread(target=my_query_filewatch)
    response_thread = threading.Thread(target=my_response_filewatch)
    
    query_thread.start()
    response_thread.start()
    
    query_thread.join()
    response_thread.join()
if __name__ == "__main__":
    run_watchers()
