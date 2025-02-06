from xml.sax.saxutils import escape
from iso3166 import countries
from .Weather import get_weather
from .Geocoder import Geocoder, get_city
from .YQL import YQL

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
    @classmethod
    def from_dict(cls, d):
        _self = cls.__new__(cls)
        for k,v in d.items():
            setattr(_self, k, v)
        return _self

    def __init__(self, yql: YQL, latlong=None, city_name=None, woeid=None, lang=None, raw_woeid=None):
        if not any([latlong, city_name, woeid]):
            raise ValueError("At least one of latlong, city_name, or woeid must be provided.")

        self.metadata = {}
        geocoder = Geocoder()

        # If WOEID is provided, get metadata and city name
        if woeid:
            self.woeid = woeid
            self.metadata = yql.get_metadata_for_woeid(woeid)
            self.city = city_name or self.metadata.get('name')
        elif city_name:
            self.city = city_name
            self.woeid = yql.get_woeid_from_name(city_name, lang=lang)
            self.metadata = yql.get_metadata_for_woeid(self.woeid)
        elif latlong:
            self.latitude, self.longitude = latlong
            location = geocoder.reverse_geocode(self.latitude, self.longitude)
            self.city = get_city(location)
            self.woeid = location.get("woeid") or yql.get_woeid_from_name(self.city, lang=lang)
            self.metadata = yql.get_metadata_for_woeid(self.woeid)

        # Ensure latlong is assigned
        if not latlong:
            latlong = geocoder.geocode(self.city, country=self.metadata.get('iso', ''))
            self.latitude, self.longitude = latlong

        self.country_alpha3 = self.metadata['iso']
        self.city = escape(self.city)
        self.location_id = "ASXX0075"
        self.state = self.metadata['state']
        weather = get_weather(self.latitude, self.longitude)
        if weather:
            self.__dict__.update(weather)
        else:
            raise ValueError("No weather data found.")
        if raw_woeid:
            self.woeid = raw_woeid