from datetime import datetime, timedelta, timezone

def moon_phase(phase):
    # New Moon
    if phase in (0, 1):
        return [0, 0]
    # First Quarter Moon
    if phase == 0.25:
        return [64, 1]
    # Full Moon
    if phase == 0.5:
        return [108, 5]
    # Last Quarter Moon
    if phase == 0.75:
        return [47, 5]
    # Waning Crescent
    if 0.75 <= phase <= 1:
        return [16, 5]
    # Waning Gibous
    if 0.50 <= phase <= 0.75:
        return [72, 5]
    # Waxing Gibous
    if 0.25 <= phase <= 0.50:
        return [84, 1]
    # Waxing Crescent
    if 0 <= phase <= 0.25:
        return [32, 1]

dateTable = {
  0: 1,
  1: 2,
  2: 3,
  3: 4,
  4: 5,
  5: 6,
  6: 7
}

def day_next(n):
    return dateTable[(datetime.now() + timedelta(days=n)).weekday()]

def day_array():
    return [
        day_next(1),
        day_next(2),
        day_next(3),
        day_next(4),
        day_next(5),
        day_next(6)
    ]

def format_poP(pop):
    if pop:
        return int(float(pop)*100)
    else:
        return 0

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