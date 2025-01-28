from datetime import datetime
from xml.sax.saxutils import escape
import time
from iso3166 import countries
from yql_x_server import Weather
from yql_x_server.Geocoder import Geocoder, get_city
from yql_x_server.YQL import YQL

def format_time_str(time_str, is_24h=True, is_12h=False):
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
    tmp = timezone_offset // 3600
    if "-" in str(tmp):
        return f"GMT{timezone_offset // 3600}"
    return f"GMT+{timezone_offset // 3600}"

class Country:
    def __init__(self, name, alpha3):
        self.alpha3 = alpha3
        self.name = escape(name)

class SearchLocation:
    def __init__(self, metadata, legacy=False):
        if metadata["iso"] not in countries:
            self.country = Country(metadata['name'], metadata['name'][0:3].upper())
        else:
            self.country = countries.get(metadata["iso"])

        name = metadata['name']
        if ", " in name and name.count(", ") == 1 and legacy:
            self.name = name.split(", ")[0]
            self.country_name = name.split(", ")[1] + ", " + self.country.name
        else:
            self.name = escape(name)
            self.country_name = escape(self.country.name)

        self.location_id = "ASXX0075"
        self.woeid = metadata['woeid']
        self.country_alpha3 = metadata['iso']

class Location:
    def __init__(self, yql: YQL, latlong=None, city_name=None, woeid=None, lang=None, raw_woeid=None):
        if not latlong and not city_name:
            raise ValueError("At least one of latlong or city_name must be provided.")

        self.metadata = {}
        if woeid and city_name:
            self.woeid = woeid
            self.metadata = yql.get_metadata_for_woeid(woeid)
            self.city = city_name
            latlong = Geocoder().geocode(self.city, country=self.metadata['iso'])
            self.latitude = latlong[0]
            self.longitude = latlong[1]
        elif woeid:
            self.woeid = woeid
            self.metadata = yql.get_metadata_for_woeid(woeid)
            self.city = self.metadata['name']
            latlong = Geocoder().geocode(self.city, country=self.metadata['iso'])
            self.latitude = latlong[0]
            self.longitude = latlong[1]
        elif city_name:
            self.city = city_name
            self.woeid = yql.get_woeid_from_name(city_name, lang=lang)
            self.metadata = yql.get_metadata_for_woeid(self.woeid)
            latlong = Geocoder().geocode(city_name, country=self.metadata['iso'])
            self.latitude = latlong[0]
            self.longitude = latlong[1]
        elif latlong:
            self.latitude = latlong[0]
            self.longitude = latlong[1]
            location = Geocoder().reverse_geocode(self.latitude, self.longitude)
            self.city = get_city(location)
            print(f"self.city: {self.city}, location: {location}")
            if "woeid" in location:
                self.woeid = location["woeid"]
                self.metadata = yql.get_metadata_for_woeid(self.woeid)
            else:
                self.woeid = yql.get_woeid_from_name(self.city, lang=lang)
                self.metadata = yql.get_metadata_for_woeid(self.woeid)
        else:
            raise ValueError("At least one of latlong or city_name must be provided.")

        self.city = escape(self.city)
        self.country_alpha3 = self.metadata['iso']
        self.state = self.metadata['state']
        weather = Weather.get_weather(self.latitude, self.longitude, self.woeid)
        self.barometer = weather['current']['pressure']
        self.currently_condition_code =  Weather.weather_icon(weather['current']['weather'][0]['id'], weather["current"]["dt"], weather['current']['sunset'])
        self.currently_condition_text = weather['current']['weather'][0]['description']
        curr_time =  Weather.weather_date(weather["current"]["dt"], weather["timezone_offset"])
        self.current_time_24h = format_time_str(curr_time)
        self.current_time_12h = format_time_str(self.current_time_24h, is_12h=True)
        self.currentDayMoonPhase =  Weather.moon_phase(float(weather['daily'][0]['moon_phase']))
        self.dew_point = weather['current']['dew_point']
        self.feels_like = weather['current']['feels_like']
        self.location_id = "ASXX0075"
        moon =  Weather.moon_phase(float(weather['daily'][0]['moon_phase']))
        self.moonfacevisible = moon[0]
        self.moonphase = moon[1]
        self.p_humidity = weather['current']['humidity']
        sunrise = Weather.weather_date(weather["current"]["sunrise"], weather["timezone_offset"])
        sunset = Weather.weather_date(weather["current"]["sunset"], weather["timezone_offset"])
        self.sunrise_24h = format_time_str(sunrise)
        self.sunset_24h = format_time_str(sunset)
        self.sunrise_12h = format_time_str(self.sunrise_24h, is_12h=True)
        self.sunset_12h = format_time_str(self.sunset_24h, is_12h=True)

        self.temp = weather['current']['temp']
        self.temp_rounded = round(self.temp)
        self.timezone = format_timezone(weather["timezone_offset"])
        if 'visibility' in weather['current']:
            self.visibility = weather['current']['visibility'] / 1000
        else:
            self.visibility = 1
        self.wind_chill = weather['current']['feels_like']
        self.wind_deg = weather['current']['wind_deg']
        self.wind_speed = weather['current']['wind_speed']

        self.days = []
        self.hours = []

        for idx in Weather.day_array():
            self.days.append(Day(idx, weather))

        for idx in range(1, 12):
            self.hours.append(Hour(weather['hourly'][idx], weather['current']['sunset'], weather['timezone_offset']))

        if raw_woeid:
            self.woeid = raw_woeid

class Day:
    def __init__(self, idx, weather):
        self.ordinal = idx

        self.currently_condition_code = Weather.weather_icon(weather['daily'][idx]['weather'][0]['id'], weather["daily"][idx]["dt"], weather['daily'][idx]['sunset'])
        self.currently_condition_text = weather['daily'][idx]['weather'][0]['description']
        self.high = weather['daily'][idx]['temp']['max']
        self.high_rounded = round(self.high)
        self.low = weather['daily'][idx]['temp']['min']
        self.low_rounded = round(self.low)
        self.pop = Weather.weather_poP(weather['daily'][idx]['pop'])

class Hour:
    def __init__(self, hour, sunset, timezone_offset):
        convTime = time.gmtime(hour['dt']+timezone_offset)
        minute = str(convTime.tm_min)
        if len(minute) == 1:
            minute = f"0{minute}"

        self.currently_condition_code = Weather.weather_icon(hour['weather'][0]['id'], hour['dt'], sunset)
        self.poP = Weather.weather_poP(hour['pop'])
        self.temp = hour['temp']
        self.time_24h = f"{str(convTime.tm_hour)}:{minute}"
