from xml.sax.saxutils import escape
from iso3166 import countries
from .Weather import get_weather
from .Geocoder import Geocoder, get_city
from .YQL import get_metadata_for_woeid, get_woeid_from_name

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

    def __init__(self, latlong=None, metadata=None, lang=None, raw_woeid=None):
        if not latlong and not metadata:
            raise ValueError("At least one of latlong or metadata must be provided.")

        geocoder = Geocoder()

        if metadata:
            self.woeid = metadata['id']
            self.city = metadata['name']
            self.country_alpha3 = metadata['iso']
            self.lang = lang
            if not latlong:
                latlong = geocoder.geocode(self.city, country=self.country_alpha3)
                self.latitude, self.longitude = latlong
            self.city = escape(self.city)
            self.metadata = metadata
        elif latlong:
            self.latitude, self.longitude = latlong
            location = geocoder.reverse_geocode(self.latitude, self.longitude)
            self.city = get_city(location)
            self.woeid = location.get("woeid") or get_woeid_from_name(self.city, lang=lang)
            self.metadata = get_metadata_for_woeid(self.woeid)
            self.country_alpha3 = self.metadata['iso']
            self.lang = lang
        else:
            raise ValueError("At least one of latlong or woeid must be provided.")
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
