import inspect
from geopy.geocoders import Nominatim, GeoNames
from .geocoder.YzuGeocoder import YzuGeocoder

class Geocoder:
    _shared_instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._shared_instance:
            cls._shared_instance = super(Geocoder, cls).__new__(cls)
        return cls._shared_instance

    def __init__(self):
        self.geocoders = [
            YzuGeocoder(),
            Nominatim(user_agent="iOSLegacyWeather", timeout=10),
            GeoNames("electimon")
        ]

    def geocode(self, city, country=None):
        for geocoder in self.geocoders:
            try:
                args = inspect.signature(geocoder.geocode).parameters
                if "country_codes" in args:
                    location = geocoder.geocode(city, country_codes=[country])
                else:
                    location = geocoder.geocode(city, country=country)
                if location:
                    return location.latitude, location.longitude
            except Exception as e:
                print(f"Failed to geocode {city} with {geocoder}, Error: {e}")
        return None, None

    def reverse_geocode(self, lat, long):
        for geocoder in self.geocoders:
            try:
                location = geocoder.reverse((lat, long)).raw
                return location
            except Exception as e:
                print(f"Failed to reverse geocode {lat}, {long} with {geocoder}, Error: {e}")
        return None

def get_city(location):
    if "toponymName" in location:
        return location['toponymName']
    if "address" in location:
        location = location['address']
    if "town" in location:
        return location['town']
    if "region" in location:
        return location['region']
    if "city" in location:
        return location['city']
    if "village" in location:
        return location['village']
    if "county" in location:
        return location['county']
    if "name" in location:
        return location['name']
    return None
