from collections import deque

_log_buffer = deque(maxlen=5000)

def ui_log(msg: str):
    _log_buffer.append(msg)

def get_ui_logs():
    return list(_log_buffer)
