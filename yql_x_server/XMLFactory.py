import re
import time
from pathlib import Path
import redis
from jinja2 import Environment, FileSystemLoader
from .stocks.StocksQParser import parseStocksXML
from .modules.YQL import get_similar_name, get_metadata_for_woeid
from .modules.Location import Location, SearchLocation
from .args import module_dir, args
from .stocks.Stocks import Symbol, get_ticker_chart_for_range, get_ticker_info

templates_path = Path(module_dir) / "templates"
env = Environment(loader = FileSystemLoader(templates_path))
modern_weather_template = env.get_template('modern_weather.jinja2')
modern_weather_search_template = env.get_template('modern_weather_search.jinja2')
legacy_weather_template = env.get_template('legacy_weather.jinja2')
legacy_weather_search_template = env.get_template('legacy_weather_search.jinja2')
stocks_getquotes_template = env.get_template('stocks_getquotes.jinja2')
stocks_getchart_template = env.get_template('stocks_getchart.jinja2')
stocks_getnews_template = env.get_template('stocks_getnews.jinja2')

if args.redis_host and args.workers > 1:
    host, _, port = args.redis_host.partition(":")
    redis_conn = redis.Redis(host=host, port=int(port) if port else None)
else:
    redis_conn = None

def format_xml(xml):
    if "None" in xml:
        print("There is a none in the xml, please fix it!")
    out = re.sub(r'\s+(?=<)', '', xml)
    return out

def store_location_in_redis(_id, location):
    if redis_conn:
        redis_conn.json().set(f"weather_{_id}", "$", location.__dict__)
        redis_conn.expire(f"weather_{_id}", 1800) # 30 minutes
    return location

def get_weather_from_redis(_id):
    if redis_conn:
        weather = redis_conn.json().get(f"weather_{_id}")
        if weather:
            return Location.from_dict(weather)
    return None

def weather_results_factory(q, latlong_in_query=False):
    _id = None

    if ("limit 1" in q and latlong_in_query) or latlong_in_query:
        if redis_conn:
            _id = abs(hash(f"{q['lat']}_{q['lon']}"))
            weather = get_weather_from_redis(_id)
            if weather:
                return [weather]

        location = Location(latlong=(q['lat'], q['lon']), lang=q['lang'])
        return [store_location_in_redis(_id, location)]
    if "limit 1" in q:
        if redis_conn:
            _id = abs(hash(q['woeids'][0]))
            weather = get_weather_from_redis(_id)
            if weather:
                return [weather]
        metadata = get_metadata_for_woeid(q['woeids'][0])
        location = Location(metadata=metadata, lang=q['lang'])
        return [store_location_in_redis(_id, location)]

    results = []
    for woeid in q['woeids']:
        if not "raw_woeids" in q:
            q['raw_woeids'] = q['woeids']

        _id = abs(hash(woeid))
        weather = get_weather_from_redis(_id)
        if weather:
            results.append(weather)
            continue

        metadata = get_metadata_for_woeid(woeid)
        location = Location(metadata=metadata, lang=q['lang'])
        results.append(store_location_in_redis(_id, location))
    return results

def search_results_factory(q, legacy=False):
    results = []
    if legacy:
        similar_results = get_similar_name(q[0], q[1])
    else:
        similar_results = get_similar_name(q['term'], q['lang'])
    for similar_result in similar_results:
        results.append(SearchLocation(similar_result, legacy=legacy))
    return results

def stocks_results_factory(q):
    results = []
    q = parseStocksXML(q)
    for symbol in q["symbols"]:
        symbol = get_ticker_info(symbol)
        if symbol:
            results.append(Symbol(symbol))
    return results

def xml_stocks_factory_dgw(q, req_type):
    match req_type:
        case "getquotes":
            symbols = stocks_results_factory(q)
            xml = stocks_getquotes_template.render({
                "type": req_type,
                "timestamp": time.time(),
                "count": len(symbols),
                "symbols": symbols,
                "advert_link": args.advert_link
            })
        case "getchart":
            _range = parseStocksXML(q)["range"]
            symbols = stocks_results_factory(q)
            if symbols:
                info: Symbol = symbols[0]
            else:
                return "Invalid ticker or range"
            ticker = info.name
            point_data = get_ticker_chart_for_range(ticker, _range)
            if not point_data:
                return "Invalid ticker or range"
            xml = stocks_getchart_template.render({
                "type": req_type,
                "timestamp": time.time(),
                "count": len(point_data),
                "symbol_name": ticker,
                "market_open": info.open,
                "market_close": info.previous_close,
                "points": point_data
            })
        case "getnews":
            symbols = stocks_results_factory(q)
            if symbols:
                info: Symbol = symbols[0]
            else:
                return "Invalid ticker or range"
            xml = stocks_getnews_template.render({
                "count": info.news_count,
                "posts": info.news
            })
        case "getsymbol":
            return xml_stocks_factory_dgw(q, "getquotes")
        case _:
            return "Invalid request type"
    return format_xml(xml)

def xml_weather_factory_yql(q: dict):
    if q['type'] == "search":
        xml = modern_weather_search_template.render({
            "results": search_results_factory(q)
        })
    elif "weather" in q['type']:
        res = weather_results_factory(q, "latlon" in q['type'])
        xml = modern_weather_template.render({
            "results": res,
            "advert_link": args.advert_link,
            "extended_forecast_url": args.advert_link,
            "count": len(res) * 2
        })
    else:
        return "Invalid request type"
    return format_xml(xml)

# DGW is inherently legacy
def xml_weather_factory_dgw(q: str, search=False):
    if search:
        xml = legacy_weather_search_template.render({
            "results": search_results_factory(q)
        })
    else:
        # It's regular weather
        xml = legacy_weather_template.render({
            "results": weather_results_factory(q),
            "advert_link": args.advert_link,
        })
    return format_xml(xml)
