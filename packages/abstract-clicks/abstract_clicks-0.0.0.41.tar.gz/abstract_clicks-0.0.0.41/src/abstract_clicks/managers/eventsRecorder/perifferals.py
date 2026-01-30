from .eventsRecorder import *
def update_events_record(default_events_path,
                         events_path):
    event_typ,exit_call = get_user_input_window()
    if not os.path.isfile(events_path):
        safe_dump_to_file(data={},
                          file_path=events_path)
    events_record = safe_load_from_file(events_path) or {}
    default_events_record = safe_load_from_file(default_events_path) or {}
    events_record[event_typ or "default"] = default_events_record.get("default")
    safe_dump_to_file(data=events_record,
                      file_path=events_path)
    if os.path.isfile(default_events_path):
        os.remov(default_events_path)
    return exit_call,events_record
def record_session(
    events_file: Optional[str] = None
) -> str:
    """
    Record events, then prompt for an event type and save mapping.
    """
    rec = EventsRecorder(events_path=events_file, refresh=True)
    rec.start_recording()
    events_path = rec.events_path
    default_events_path = rec.default_events_path
    exit_call,events_record = update_events_record(default_events_path,
                                                   events_path)
    return exit_call,events_record


def replay_session(
    event_type: str,
    events_file: Optional[str] = None
) -> None:
    rec = EventsRecorder(events_path=events_file)
    rec.replay(event_type)
