from datetime import datetime, timedelta, timezone
import time

def format_time_str(time_str, is_24h=True, is_12h=False):
    if isinstance(time_str, datetime):
        return time_str.strftime("%I:%M %p") if is_12h else time_str.strftime("%H:%M")
    
    if is_12h:
        _time = datetime.strptime(time_str, "%H:%M")
        return _time.strftime("%I:%M %p")
    
    if is_24h:
        if 'AM' in time_str or 'PM' in time_str:
            _time = datetime.strptime(time_str, "%I:%M %p")
        else:
            _time = datetime.strptime(time_str, "%H:%M")
        return _time.strftime("%H:%M")
    
    return time_str

def format_timezone(timezone_offset):
    tz = timezone(timedelta(seconds=timezone_offset))
    now = datetime.now(tz)
    offset = now.strftime("%z")
    hours = int(offset[:3])
    return f"GMT{hours}" if hours < 0 else f"GMT+{hours}"