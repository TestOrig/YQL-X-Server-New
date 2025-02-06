from .ModuleClasses import Weather
from .weather.OWMWeather import OWMWeather
from .weather.YzuWeather import YzuWeather
from ..args import args
import redis

if args.redis_host and args.workers > 1:
    host, _, port = args.redis_host.partition(":")
    redis_conn = redis.Redis(host=host, port=int(port) if port else None)
else:
    redis_conn = None

available_providers = [
    OWMWeather,
    YzuWeather,
]

if args.owm_key is None:
    available_providers.remove(OWMWeather)

available_providers = [provider() for provider in available_providers]

weatherObj = Weather(available_providers)

def get_weather(lat, lon):
    _id = None
    if redis_conn:
        _id = abs(hash(f"{lat}_{lon}"))
        weather = redis_conn.json().get(f"weather_{_id}")
        if weather is not None:
            return weather
    result = weatherObj.get_weather(lat, lon)
    if redis_conn:
        redis_conn.json().set(f"weather_{_id}", "$", result)
        redis_conn.expire(f"weather_{_id}", 3600)
    return result