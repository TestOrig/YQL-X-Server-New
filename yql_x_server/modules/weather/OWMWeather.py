import time
import requests
from ..Weather import Weather
from ...args import args
from ...utils import *

class OWMWeather(Weather):
    def __init__(self):
        super().__init__()

    def get_weather_dict(self, lat, lng):
        _key = f"{lat},{lng}"
        data = self.retrieve(_key)
        if data:
            return data

        uri = 'https://api.openweathermap.org/data/3.0/onecall'
        querystring = {
            "lat": lat, "lon": lng,
            "exclude": "alerts,minutely",
            "units": "metric",
            "appid": args.owm_key
        }
        response = (requests.request("GET", uri, params=querystring, timeout=5)).json()
        if response and "cod" not in response:
            out = self.format_to_loc(response)
            self.store(out, _key)
            return out
        # TODO, None handling lmao
        return None

    def format_to_loc(self, data):
        moon_info = moon_phase(float(data["daily"][0]["moon_phase"]))
        
        curr_time = format_time_with_offset(data["current"]["dt"], data["timezone_offset"])
        sunrise = format_time_with_offset(data["current"]["sunrise"], data["timezone_offset"])
        sunset = format_time_with_offset(data["current"]["sunset"], data["timezone_offset"])

        for idx in day_array():
            self.days.append({
                "ordinal": idx,
                "currently_condition_code": weather_icon(data["daily"][idx]["weather"][0]["id"], data["daily"][idx]["dt"], data["daily"][idx]["sunset"]),
                "currently_condition_text": data["daily"][idx]["weather"][0]["description"],
                "high": data["daily"][idx]["temp"]["max"],
                "high_rounded": round(data["daily"][idx]["temp"]["max"]),
                "low": data["daily"][idx]["temp"]["min"],
                "low_rounded": round(data["daily"][idx]["temp"]["min"]),
                "poP": format_poP(data["daily"][idx]["pop"])
            })

        for idx in range(1, 12):
            convTime = time.gmtime(data["hourly"][idx]['dt']+data["timezone_offset"])
            minute = str(convTime.tm_min)
            if len(minute) == 1:
                minute = f"0{minute}"
            self.hours.append({
                "currently_condition_code": weather_icon(data["hourly"][idx]["weather"][0]["id"], data["hourly"][idx]["dt"], data["current"]["sunset"]),
                "poP": format_poP(data["hourly"][idx]["pop"]),
                "temp": data["hourly"][idx]["temp"],
                "time_24h": f"{str(convTime.tm_hour)}:{minute}"
            })

        out = {
            "barometer": data["current"]["pressure"],
            "currently_condition_code": weather_icon(data["current"]["weather"][0]["id"], data["current"]["dt"], data["current"]["sunset"]),
            "currently_condition_text": data["current"]["weather"][0]["description"],
            "current_time_12h": format_time_str(curr_time, is_12h=True),
            "current_time_24h": format_time_str(curr_time),
            "days": self.days,
            "dew_point": data["current"]["dew_point"],
            "feels_like": data["current"]["feels_like"],
            "hours": self.hours,
            "moonfacevisible": moon_info[0],
            "moonphase": moon_info[1],
            "p_humidity": data["current"]["humidity"],
            "sunrise_12h": format_time_str(sunrise, is_12h=True),
            "sunrise_24h": format_time_str(sunrise),
            "sunset_12h": format_time_str(sunset, is_12h=True),
            "sunset_24h": format_time_str(sunset),
            "temp": data["current"]["temp"],
            "temp_rounded": round(data["current"]["temp"]),
            "timezone": format_timezone(data["timezone_offset"]),
            "visibility": data["current"].get("visibility", 1000) / 1000,
            "wind_chill": data["current"]["feels_like"],
            "wind_deg": data["current"]["wind_deg"],
            "wind_speed": data["current"]["wind_speed"]
        }
        return out

def format_time_with_offset(dt, timezone_offset):
    currTime = time.gmtime(dt+timezone_offset)
    return f"{str(currTime.tm_hour)}:{str(currTime.tm_min)}"

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
