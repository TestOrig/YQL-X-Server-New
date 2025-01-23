import datetime
import time
import requests
from cachetools import TTLCache
from yql_x_server.args import args

# Initialize a cache with a time-to-live (TTL) of 1 hour (3600 seconds)
woeidCache = TTLCache(maxsize=100, ttl=3600)

dateTable = {
  0: 1,
  1: 2,
  2: 3,
  3: 4,
  4: 5,
  5: 6,
  6: 7
}

# Helper Functions
def get_latlong_for_q(q):
    latIndex1 = q.index('lat=')+4
    latIndex2 = q.index(' and')
    longIndex1 = q.index('lon=')+4
    longIndex2 = q.index(' and', latIndex2+3)
    lat = q[latIndex1:latIndex2]
    long = q[longIndex1:longIndex2-1]
    print("lat = " + lat)
    print("long = " + long)
    print("longIndex1 = " + q)
    return [lat, long]

def get_weather(lat, lng, woeid):
    # We will try to see if a cached response is in the cache, if so and the timestamp matches
    # we will return that instead of abusing the API :)
    if woeid in woeidCache:
        cached_response = woeidCache[woeid]
        if cached_response['timestamp'] == datetime.datetime.now().strftime("%Y-%m-%d %H"):
            print("Returning cached response")
            return cached_response['response']
    uri = 'https://api.openweathermap.org/data/3.0/onecall'
    querystring = {"lat": lat, "lon": lng,
     "exclude": "alerts,minutely",
     "units": "metric",
     "appid": args.owm_key}
    response = (requests.request("GET", uri, params=querystring, timeout=5)).json()
    if response:
        woeidCache[woeid] = {
            "response": response,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H")
        }
        return response
    # TODO, None handling lmao
    return None

##
# 0 = lightning
# 6 = rain&snow
# 9 = rain&clouds
# 11 = rain
# 13 = flurries
# 15 = snow
# 17 = hail
# 19 = sun&haze
# 23 = haze
# 25 = ice
# 27 = Clouds/Cloudy
# 29 = moon&partlycloudy
# 30 = sun&partlycloudy
# 31 = moon
# 32 = sun
# 33 = mooncloud
# 34 = suncloud
# 35 = rain&snow
# 37 = sun&lightning
# 39 = sun&rain
# 42 = ice&snow
# 44 = sun&partlycloudy
# 46 = ice&snow
# 48 =

def weather_icon(_id, timestamp, sunset):
    day = timestamp < sunset
    _id = str(_id)
    if _id.startswith("2"):  # Thunderstorm
        return 0  # Lightning
    if _id.startswith("3"):  # Drizzle
        return 9
    if _id.startswith("5"):  # Rain
        if _id == "500":  # Light rain
            return 39 if day else 9
        if _id == "501":  # Moderate rain
            return 11
        if _id in ["502", "503", "504"]:  # Heavy intensity rain
            return 11
        if _id == "511":  # Freezing rain
            return 25
        if _id.startswith("52"):  # Shower rain
            return 11
    if _id.startswith("6"):  # Snow
        if _id in ["600", "620"]:  # Light snow
            return 13
        if _id in ["601", "621"]:  # Snow
            return 15
        if _id in ["602", "622"]:  # Heavy snow
            return 46
        if _id in ["611", "612", "613"]:  # Sleet
            return 6
        if _id in ['615', '616']:  # Rain and snow
            return 35
    if _id.startswith("7"):  # Atmosphere (Mist, Smoke, Haze, etc.)
        if _id == "781":  # Tornado
            return 0  # No specific icon for tornado, using lightning
        return 23  # Use the same icon for all misty conditions
    if _id.startswith("8"):  # Clear and clouds
        if _id == "800":  # Clear sky
            return 32 if day else 31
        if _id == "801":  # Few clouds
            return 30 if day else 29
        if _id == "802":  # Scattered clouds
            return 30 if day else 29
        if _id in ['803', '804']:  # Broken clouds, overcast clouds
            return 27
    # Additional codes for extreme weather conditions can be added here with proper mappings
    # As an example, adding a few more:
    if _id.startswith("9"):  # Extreme
        if _id in ["900", "901", "902", "962"]: # Tornado + hurricanes
            return 0
        if _id == "903":  # Cold
            return 25
        if _id == "904":  # Hot
            return 19
        if _id == "905":  # Windy
            return 23
        if _id == "906":  # Hail
            return 17
    # Unknown or not assigned codes:
    return 48  # You can use this as a default 'unknown' code

def weather_poP(pop):
    return int(float(pop)*100)

def weather_date(dt, timezone_offset):
    currTime = time.gmtime(dt+timezone_offset)
    return f"{str(currTime.tm_hour)}:{str(currTime.tm_min)}"

# My brain is big for the next 2 functions
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

# Mapping OWM moon phases
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
