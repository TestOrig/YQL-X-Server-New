from datetime import datetime
import time
from iso3166 import countries
from yql_x_server.Weather import getWeather, weatherIcon, weatherPoP, weatherDate, moonPhase, dayArray
from yql_x_server.Geocoder import Geocoder, getCity
from yql_x_server.YQL import YQL

def format_time_str(time_str, is_24h=True, is_12h=False):
    if is_12h:
        time = datetime.strptime(time_str, "%H:%M")
        return time.strftime("%I:%M %p")
    if is_24h:
        if 'AM' in time_str or 'PM' in time_str:
            time = datetime.strptime(time_str, "%I:%M %p")
        else:
            time = datetime.strptime(time_str, "%H:%M")
        return time.strftime("%H:%M")

def format_timezone(timezone_offset):
    tmp = timezone_offset // 3600
    if "-" in str(tmp):
        return f"GMT{timezone_offset // 3600}"
    else:
        return f"GMT+{timezone_offset // 3600}"

class Country:
    def __init__(self, name, alpha3):
        self.alpha3 = alpha3
        self.name = name

class SearchLocation:
    def __init__(self, metadata):
        if metadata["iso"] not in countries:
            self.country = Country(metadata['name'], metadata['name'][0:3].upper())
        else:
            self.country = countries.get(metadata["iso"])

        self.country_name = self.country.name
        self.location_id = "ASXX0075"
        self.name = metadata['name']
        self.woeid = metadata['woeid']

class Location:
    def __init__(self, yql: YQL, latlong=None, city_name=None, woeid=None):
        if not latlong and not city_name:
            raise ValueError("At least one of latlong or city_name must be provided.")

        if latlong and city_name:
            self.latitude = latlong[0]
            self.longitude = latlong[1]
            self.city = city_name
        elif latlong:
            self.latitude = latlong[0]
            self.longitude = latlong[1]
            location = Geocoder().reverse_geocode(self.latitude, self.longitude)
            self.city = getCity(location)
            if "woeid" in location:
                woeid = location["woeid"]
        else:
            self.city = city_name
            latlong = Geocoder().geocode(city_name)
            self.latitude = latlong[0]
            self.longitude = latlong[1]

        if woeid:
            self.woeid = woeid
        else:
            self.woeid = yql.getWoeidFromName(self.city)
        weather = getWeather(self.latitude, self.longitude, self.woeid)

        self.barometer = weather['current']['pressure']
        self.currently_condition_code = weatherIcon(weather['current']['weather'][0]['id'], weather["current"]["dt"], weather['current']['sunset'])
        self.currently_condition_text = weather['current']['weather'][0]['description']
        currTime = weatherDate(weather["current"]["dt"], weather["timezone_offset"])
        self.current_time_24h = format_time_str(currTime)
        self.current_time_12h = format_time_str(self.current_time_24h, is_12h=True)
        self.currentDayMoonPhase = moonPhase(float(weather['daily'][0]['moon_phase']))
        self.dew_point = weather['current']['dew_point']
        self.feels_like = weather['current']['feels_like']
        self.location_id = "ASXX0075"
        moon = moonPhase(float(weather['daily'][0]['moon_phase']))
        self.moonfacevisible = moon[0]
        self.moonphase = moon[1]
        self.p_humidity = weather['current']['humidity']
        sunrise = weatherDate(weather["current"]["sunrise"], weather["timezone_offset"])
        sunset = weatherDate(weather["current"]["sunset"], weather["timezone_offset"])
        self.sunrise_24h = format_time_str(sunrise)
        self.sunset_24h = format_time_str(sunset)
        self.sunrise_12h = format_time_str(self.sunrise_24h, is_12h=True)
        self.sunset_12h = format_time_str(self.sunset_24h, is_12h=True)

        self.temp = weather['current']['temp']
        self.temp_rounded = round(self.temp)
        self.timezone = format_timezone(weather["timezone_offset"])
        self.visibility = weather['current']['visibility'] / 1000
        self.wind_chill = weather['current']['feels_like']
        self.wind_deg = weather['current']['wind_deg']
        self.wind_speed = weather['current']['wind_speed']

        self.days = []
        self.hours = []

        for idx in dayArray():
            self.days.append(Day(idx, weather))

        for idx in range(1, 12):
            self.hours.append(Hour(weather['hourly'][idx], weather['current']['sunset'], weather['timezone_offset']))

class Day:
    def __init__(self, idx, weather):
        self.ordinal = idx

        self.currently_condition_code = weatherIcon(weather['daily'][idx]['weather'][0]['id'], weather["daily"][idx]["dt"], weather['daily'][idx]['sunset'])
        self.currently_condition_text = weather['daily'][idx]['weather'][0]['description']
        self.high = weather['daily'][idx]['temp']['max']
        self.high_rounded = round(self.high)
        self.low = weather['daily'][idx]['temp']['min']
        self.low_rounded = round(self.low)
        self.pop = weatherPoP(weather['daily'][idx]['pop'])

class Hour:
    def __init__(self, hour, sunset, timezone_offset):
        convTime = time.gmtime(hour['dt']+timezone_offset)
        minute = str(convTime.tm_min)
        if len(minute) == 1:
            minute = f"0{minute}"

        self.currently_condition_code = weatherIcon(hour['weather'][0]['id'], hour['dt'], sunset)
        self.poP = weatherPoP(hour['pop'])
        self.temp = hour['temp']
        self.time_24h = f"{str(convTime.tm_hour)}:{minute}"
