import argparse
import os

module_dir = os.path.dirname(__file__)

# Args
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--host", type=str, default="0.0.0.0")
parser.add_argument("--generated_woeids_path", type=str, default=os.path.join(module_dir, "generatedWoeids.json"), help="In earlier versions of this server, there were woeid misses, so the decision was made to generate them based on ord() of the characters in the city name. This is the path to the generated woeids file, you shouldn't need to touch this.")
parser.add_argument("--yzugeo_server", type=str, default="https://apis.yzu.moe/yzugeo/v1", help="Development use only, the server to use for geocoding via the YzuGeo provider")
parser.add_argument("--yzugeo_weather_server", type=str, default="https://apis.yzu.moe/weather/v1/forecast", help="API path for Electimon's weather server")
parser.add_argument("--owm_key", type=str, help="OpenWeatherMap API Key")
parser.add_argument("--advert_link", type=str, default="https://yzu.moe", help="Inside the app there are some links to Yahoo and whatever else, this controls the links provided by this server. The default is my website :)")
parser.add_argument("--sentry_url", type=str, default=None, help="Sentry DSN URL, if you wish to report errors to sentry")
parser.add_argument("--workers", type=int, default=1, help="Number of workers to use")
parser.add_argument("--redis_host", type=str, default=None, help="If you specify this, and workers > 1, the server will use redis (json) for inter-process by the hour caching")
args = parser.parse_args()