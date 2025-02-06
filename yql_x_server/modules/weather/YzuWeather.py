import pytz
import ephem
import requests
from datetime import datetime as dt, timezone, date
from ..Weather import Weather
from ...utils import *
from ...args import args

class YzuWeather(Weather):
    def __init__(self):
        super().__init__()
        self.prefix_days = 2
        self.prefix_hours = (self.prefix_days * 24) - 1 # starting idx is 0
        self.current_time: dt = None
        self.sunrise_today: dt = None
        self.sunset_today: dt = None
        self.data = None

    def query_builder(self, lat, lng):
        vars = {
            "latitude": lat,
            "longitude": lng,
            "hourly": ",".join([
                "temperature_2m",
                "apparent_temperature",
                "precipitation_probability",
                "weather_code",
                "is_day"
            ]),
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "weather_code",
                "sunset",
                "sunrise",
                "precipitation_probability_mean"
            ]),
            "current": ",".join([
                "pressure_msl",
                "dew_point_2m",
                "apparent_temperature",
                "precipitation_probability",
                "temperature_2m",
                "wind_direction_10m",
                "wind_speed_10m",
                "weather_code",
                "relative_humidity_2m",
                "visibility"
            ]),
            "timeformat": "unixtime",
            "timezone": "auto",
            "past_days": self.prefix_days
        }
        return vars

    def _normalize_time(self, time: int, data):
        return dt.fromtimestamp(time, dt.now(timezone.utc).astimezone().tzinfo).astimezone(pytz.timezone(data["timezone"]))

    def get_weather_dict(self, lat, lng):
        _key = f"{lat},{lng}"
        data = self.retrieve(_key)
        if data:
            print("Using cached weather data")
            return data
        uri = args.yzugeo_weather_server
        #uri = 'https://api.open-meteo.com/v1/forecast'
        querystring = self.query_builder(lat, lng)
        response = (requests.request("GET", uri, params=querystring, timeout=15)).json()
        if response and "hourly" in response and "daily" in response and "current" in response:
            for idx, hour in enumerate(response["hourly"]["time"]):
                response["hourly"]["time"][idx] = self._normalize_time(hour, response)
            for idx, day in enumerate(response["daily"]["time"]):
                response["daily"]["time"][idx] = self._normalize_time(day, response)
            for idx, day in enumerate(response["daily"]["sunrise"]):
                response["daily"]["sunrise"][idx] = self._normalize_time(day, response)
            for idx, day in enumerate(response["daily"]["sunset"]):
                response["daily"]["sunset"][idx] = self._normalize_time(day, response)
            response["current"]["time"] = self._normalize_time(response["current"]["time"], response)
            self.fill_self(response)
            out = self.format_to_loc(response)
            self.store(out, _key)
            return out
        # TODO, None handling lmao
        return None

    def _get_currently_weather_code(self, data, day, hour):
        ret = weather_icon(data["current"]["weather_code"], data["current"]["time"] < data["daily"]["sunset"][day])
        if ret == -1:
            if hour != 0:
                return self._get_weather_code_for_hour(data, hour)
            return 48
        return ret
    
    def _get_weather_code_for_hour(self, data, hour):
        hourly_data = data.get("hourly", {})
        weather_code = hourly_data["weather_code"][hour]
        ret = weather_icon(weather_code, data["hourly"]["is_day"][hour])
        if ret == -1:
            return self._get_weather_code_for_hour(data, hour-1)
        return ret

    def _get_weather_code_for_day(self, data, day):
        curr: dt = data["daily"]["time"][day]
        hour_idx =  curr.hour + self.prefix_hours + day * 24
        ret = weather_icon(data["daily"]["weather_code"][day], curr < data["daily"]["sunset"][day])
        if ret == -1:
            return self._get_weather_code_for_hour(data, hour_idx-1)
        return ret

    def fill_self(self, data): # this function exists to type hint the data
        self.data = data
        self.current_time = self.data["current"]["time"]
        self.sunrise_today = self.data["daily"]["sunrise"][0]
        self.sunset_today = self.data["daily"]["sunset"][0]

    def format_to_loc(self, data):
        moonphase = get_phase_on_day(self.current_time.year, self.current_time.month, self.current_time.day)
        moonphase_percent = int(round(moonphase * 100, 0))
        moon_info = moon_phase(moonphase)
        day_idx = self.current_time.weekday()
        hour_idx = self.current_time.hour + self.prefix_hours
        visibility = int(((data["current"].get("visibility") or 100)) / 100)
        feels_like = self.data["current"].get("apparent_temperature")
        if not feels_like:
            feels_like = data["current"].get("temperature_2m")
        wind_chill = feels_like

        for idx in day_array():
            poP = data["daily"]["precipitation_probability_mean"][idx]
            if poP is None:
                poP = 0
            self.days.append({
                "ordinal": idx,
                "currently_condition_code": self._get_weather_code_for_day(data, idx),
                "currently_condition_text": "",
                "high": data["daily"]["temperature_2m_max"][idx],
                "high_rounded": round(data["daily"]["temperature_2m_max"][idx]),
                "low": data["daily"]["temperature_2m_min"][idx],
                "low_rounded": round(data["daily"]["temperature_2m_min"][idx]),
                "poP": poP
            })

        for idx in range(hour_idx+1, hour_idx+12):
            curr_time: dt = data["hourly"]["time"][idx]
            minute = str(curr_time.minute)
            poP = data["hourly"]["precipitation_probability"][idx]
            if poP is None:
                poP = 0
            if len(minute) == 1:
                minute = f"0{minute}"
            self.hours.append({
                "currently_condition_code": self._get_weather_code_for_hour(data, idx),
                "poP": poP,
                "temp": data["hourly"]["temperature_2m"][idx],
                "time_24h": f"{curr_time.hour}:{minute}"
            })

        out = {
            "barometer": int(data["current"]["pressure_msl"]),
            "currently_condition_code": self._get_currently_weather_code(data, day_idx, hour_idx),
            "currently_condition_text": "",
            "current_time_12h": self.current_time.strftime("%I:%M %p"),
            "current_time_24h": self.current_time.strftime("%H:%M"),
            "days": [i for i in self.days],
            "dew_point": data["current"]["dew_point_2m"],
            "feels_like": feels_like,
            "hours": [i for i in self.hours],
            "moonfacevisible": moonphase_percent,
            "moonphase": moon_info[1],
            "p_humidity": data["current"]["relative_humidity_2m"],
            "sunrise_12h": self.sunrise_today.strftime("%I:%M %p"),
            "sunrise_24h": self.sunrise_today.strftime("%H:%M"),
            "sunset_12h": self.sunset_today.strftime("%I:%M %p"),
            "sunset_24h": self.sunset_today.strftime("%H:%M"),
            "temp": data["current"]["temperature_2m"],
            "temp_rounded": round(data["current"]["temperature_2m"]),
            "timezone": format_timezone(data["utc_offset_seconds"]),
            "visibility": visibility,
            "wind_chill": wind_chill,
            "wind_deg": data["current"].get("wind_direction_10m", 0),
            "wind_speed": data["current"].get("wind_speed_10m", 0)
        }

        return out

    def get_days(self):
        return self.days
    
    def get_hours(self):
        return self.hours

##
# 0 = nothing
# 1 = lightning
# 2 = lightning
# 3 = lightning
# 4 = rain&snow
# 5 = rain&snow
# 6 = rain&snow
# 7 = rain&snow
# 8 = less than normal sized cloud with rain
# 9 = less than normal sized cloud with rain
# 10 = poppy circular hail? and frozen
# 11 = rain with no clouds
# 12 = rain with no clouds
# 13 = flurries (frozen?)
# 14 = flurries (frozen?)
# 15 = snow (with ice)
# 16 = snow (with ice)
# 17 = same as 10
# 18 = same as 10
# 19 = sun&haze
# 20 = haze
# 21 = sun&haze
# 22 = sun&haze
# 23 = haze+fog?
# 24 = haze+fog?
# 25 = mild ice
# 26 = tiny summer clouds
# 27 = tiny summer clouds
# 28 = tiny summer clouds
# 29 = moon&partlycloudy
# 30 = sun&partlycloudy
# 31 = moon
# 32 = sun
# 33 = mooncloud - same as 29
# 34 = suncloud - same as 30
# 35 = rain&snow
# 36 - sun?
# 37 = sun&lightning
# 38 = sun&lightning
# 39 = sun&rain (actually sun&lightning)
# 40 = downpour same as 11 and 12
# 41 = ice&snow
# 42 = ice&snow
# 43 = ice&snow
# 44 = sun&partlycloudy
# 45 = sun&lightning (scary)
# 46 = ice&snow
# 47 = sun&lightning (scary)
# 48 = lightning no sun

def weather_icon(_id, day):
    _id = int(_id)
    if _id == 19:  # Tornado
        return 1  # No specific icon for tornado, using lightning
    if _id in [17, 29, 95, 96, 97, 98, 99, 13]:  # Thunderstorm
        return 1  # Lightning
    if _id in [20, 91] + list(range(50,57)):  # Drizzle
        return 9
    if _id in [58, 59, 68, 69, 60, 61, 80]:  # Light rain
        return 9 if day else 8
    if _id in [57, 62, 63, 21, 92]:  # Moderate rain
        return 11
    if _id in [64, 65, 82]:  # Heavy intensity rain
        return 11
    if _id in [66, 67, 24]:  # Freezing rain
        return 25
    if _id in [25, 81]:  # Shower rain
        return 11
    if _id in [36, 70, 71, 76, 77, 78, 85]:  # Light snow
        return 13
    if _id in [22, 72, 73, 86]:  # Snow
        return 15
    if _id in [37, 38, 39, 74, 75, 94]:  # Heavy snow
        return 46
    if _id in [23, 26, 83, 84, 93]:  # Rain and snow
        return 35
    if _id in [4, 5, 6, 7, 8, 9, 10, 11, 12, 28] + list(range(30,36)) + list(range(40,49)):
        return 23  # Use the same icon for all misty conditions
    if _id in [0, 1]:  # Clear sky
        return 32 if day else 31
    if _id in [2]:  # Few clouds
        return 34 if day else 33
    if _id in [3]:  # Scattered clouds
        return 27 if day else 26
    if _id in [13, 14, 15, 16]:  # Broken clouds
        return 27
    if _id in [18]:  # Windy
        return 23
    if _id in [27, 79, 87, 88, 89, 90]:  # Hail
        return 17
    return -1

# https://stackoverflow.com/questions/2526815/moon-lunar-phase-algorithm
def get_phase_on_day(year: int, month: int, day: int):
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