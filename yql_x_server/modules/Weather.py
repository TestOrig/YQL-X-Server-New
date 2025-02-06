from .ModuleClasses import Weather
from .weather.OWMWeather import OWMWeather
from .weather.YzuWeather import YzuWeather
from ..args import args

available_providers = [
    OWMWeather,
    YzuWeather,
]

if args.owm_key is None:
    available_providers.remove(OWMWeather)

def get_weather(lat, lon):
    return Weather(available_providers).get_weather(lat, lon)