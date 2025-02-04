import datetime

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
    return dateTable[(datetime.datetime.now() + datetime.timedelta(days=n)).weekday()]

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