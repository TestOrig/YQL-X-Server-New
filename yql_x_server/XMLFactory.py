import re
from pathlib import Path
import time
from jinja2 import Environment, FileSystemLoader
from yql_x_server.StocksQParser import parseStocksXML
from yql_x_server.YQL import YQL
from yql_x_server.Location import Location, SearchLocation
from yql_x_server.args import module_dir, args
from yql_x_server.Stocks import Symbol, get_ticker_chart_for_range, get_ticker_info

templates_path = Path(module_dir) / "templates"
env = Environment(loader = FileSystemLoader(templates_path))
modern_weather_template = env.get_template('modern_weather.jinja2')
modern_weather_search_template = env.get_template('modern_weather_search.jinja2')
legacy_weather_template = env.get_template('legacy_weather.jinja2')
legacy_weather_search_template = env.get_template('legacy_weather_search.jinja2')
stocks_getquotes_template = env.get_template('stocks_getquotes.jinja2')
stocks_getchart_template = env.get_template('stocks_getchart.jinja2')
stocks_getnews_template = env.get_template('stocks_getnews.jinja2')

def format_xml(xml):
    return re.sub(r'\s+(?=<)', '', xml)

def weather_results_factory(q, yql: YQL, latlong_in_query=False):
    if "limit 1" in q and latlong_in_query:
        return [Location(yql, latlong=(q['lat'], q['lon']), lang=q['lang'])]
    elif "limit 1" in q:
        city = yql.get_names_for_woeids_in_q(q, nameInQuery=True)
        return [Location(yql, city_name=city[0], lang=q['lang'])]
    elif latlong_in_query:
        return [Location(yql, latlong=(q['lat'], q['lon']), lang=q['lang'])]
    results = []
    cities = yql.get_names_for_woeids_in_q(q)
    for i, _ in enumerate(cities):
        if latlong_in_query:
            results.append(Location(yql, latlong=(q["lat"], q["lon"])))
        else:
            print(f"Adding {cities[i]} to results")
            if not "raw_woeids" in q:
                q['raw_woeids'] = q['woeids']
            results.append(
                Location(
                    yql,
                    city_name=cities[i],
                    woeid=q['woeids'][i],
                    raw_woeid=q['raw_woeids'][i],
                    lang=q['lang'],
                )
            )
    return results

def search_results_factory(q, yql: YQL, legacy=False):
    results = []
    if legacy:
        similar_results = yql.get_similar_name(q[0], q[1])
    else:
        similar_results = yql.get_similar_name(q['term'], q['lang'])
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

def xml_weather_factory_yql(q: dict, yql: YQL):
    if q['type'] == "search":
        xml = modern_weather_search_template.render({
            "results": search_results_factory(q, yql)
        })
    elif "weather" in q['type']:
        res = weather_results_factory(q, yql, "latlon" in q['type'])
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
def xml_weather_factory_dgw(q: str, yql: YQL, search=False):
    if search:
        xml = legacy_weather_search_template.render({
            "results": search_results_factory(q, yql)
        })
    else:
        # It's regular weather
        xml = legacy_weather_template.render({
            "results": weather_results_factory(q, yql),
            "advert_link": args.advert_link,
        })
    return format_xml(xml)
