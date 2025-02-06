from datetime import datetime, timedelta, timezone, date
import html
import json
from pathlib import Path
import re
import threading
import ephem
from .args import args

gen_file_lock = threading.Lock()

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

# https://stackoverflow.com/questions/2526815/moon-lunar-phase-algorithm
def get_moon_phase_for_date(year: int, month: int, day: int):
    """Returns a floating-point number from 0-1. where 0=new, 0.5=full, 1=new"""
    #Ephem stores its date numbers as floating points, which the following uses
    #to conveniently extract the percent time between one new moon and the next
    #This corresponds (somewhat roughly) to the phase of the moon.

    #Use Year, Month, Day as arguments
    _date = ephem.Date(date(year,month,day))

    nnm = ephem.next_new_moon(_date)
    pnm = ephem.previous_new_moon(_date)

    lunation = (_date-pnm)/(nnm-pnm)

    #Note that there is a ephem.Moon().phase() command, but this returns the
    #percentage of the moon which is illuminated. This is not really what we want.

    return lunation

def get_woeids_in_query(q, formatted=False, legacy=False):
    if formatted:
        return [q] if not isinstance(q, list) else q
    woeids = []
    if legacy:
        # It's an XML document
        for item in q.iter("id"):
            woeids.append(item.text)
        return woeids
    for woeid in re.findall(r'\b\d+\b', q):
        if not woeid in woeids:
            woeids.append(woeid)
    return woeids

def get_legacy_woeids_in_q(q, keep_prefix=False):
    woeids = []
    # It's an XML document
    for item in q.iter("id"):
        if "|" in item.text and not keep_prefix:
            woeids.append(item.text.split("|")[1])
        else:
            woeids.append(item.text)
    return woeids

def parse_query(q, legacy=False):
    if legacy:
        _type = q[0].attrib['type']
        if _type == "getlocationid":
            # search case
            result = {"term": q[0][0].text, "lang": q[0][1].text, "type": "search"}
            print(f"Parsing query: {q}, result: {result}")
            return result
        result = {}
        result['woeids'] = get_legacy_woeids_in_q(q)
        result['raw_woeids'] = get_legacy_woeids_in_q(q, keep_prefix=True)
        result['type'] = "weather/woeid"
        result['lang'] = q[0][1].text
        print(f"Parsing query: {q}, result: {result}")
        return result
    q = html.unescape(q)
    result = {'lang': re.search(r"lang='([^']+)'", q).group(1)}
    if 'partner.weather.locations' in q and not 'yql.query.multi' in q:
        result['term'] = re.search(r'query="([^"]+)"', q).group(1)
        result['type'] = "search"
    elif "lat=" in q and "lon=" in q:
        result['lat'] = re.search(r'lat=(-?\d+\.\d+)', q).group(1)
        result['lon'] = re.search(r'lon=(-?\d+\.\d+)', q).group(1)
        result['type'] = "weather/latlon"
    elif "woeid" in q:
        woeids = []
        for woeid in re.findall(r'woeid=(\d+)', q):
            if not woeid in woeids:
                woeids.append(woeid)
        result['woeids'] = woeids
        if not result['woeids']:
            for woeid in re.findall(r'woeid.*?(\d+)', q):
                if not woeid in woeids:
                    woeids.append(woeid)
            result['woeids'] = woeids
        result['type'] = "weather/woeid"
    result['lang'] = re.search(r"lang='([^']+)'", q).group(1)
    print(f"Parsing query: {q}, result: {result}")
    return result

def gen_woeid_for_name(name):
    # Generate woeid from name, store the characters in unicode int format for decoding later
    print("Generating woeid from name, " + name)
    with gen_file_lock:
        generated_file = open(Path(args.generated_woeids_path), "r+", encoding='utf-8')
        generated_woeids = json.load(generated_file)
        woeid = ""
        woeid_array = []
        for letter in name:
            unicode = str(ord(letter))
            woeid += unicode
            woeid_array.append(unicode)
        if not any(woeid in v for v in generated_woeids):
            print("Adding woeid to generatedWoeids.json")
            generated_woeids.update({woeid: woeid_array})
            generated_file.seek(0)
            generated_file.write(json.dumps(generated_woeids))
            generated_file.truncate()
        else:
            print("Woeid already in generatedWoeids.json")
        generated_file.close()
        return woeid

def get_gen_name_for_woeid(woeid):
    print(f"Failed to get name for {woeid}")
    generated_file = open(Path(args.generated_woeids_path), "r", encoding='utf-8')
    generated_woeids = json.load(generated_file)
    if not generated_woeids:
        generated_file.close()
        return None
    name = ""
    for unicode_char in generated_woeids[woeid]:
        name += chr(int(unicode_char))
    generated_file.close()
    return name
