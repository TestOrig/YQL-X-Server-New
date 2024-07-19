from geopy.geocoders import Nominatim, GeoNames

class Geocoder:
    _shared_instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._shared_instance:
            cls._shared_instance = super(Geocoder, cls).__new__(cls)
        return cls._shared_instance
  
    def __init__(self):
        self.geocoders = [
            Nominatim(user_agent="iOSLegacyWeather", timeout=10),
            GeoNames("electimon")
        ]

    def geocode(self, city):
        for geocoder in self.geocoders:
            try:
                location = geocoder.geocode(city)
                if location:
                    return location.latitude, location.longitude
            except:
                continue
        return None, None
 
    def reverse_geocode(self, lat, long):
        for geocoder in self.geocoders:
            try:
                location = geocoder.reverse((lat, long)).raw
                return location
            except:
                continue
        return None

def getCity(location):
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
    return None
