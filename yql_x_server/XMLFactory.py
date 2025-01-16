import re
from pathlib import Path
import time
from jinja2 import Environment, FileSystemLoader
from yql_x_server.Blog import GetBlogPosts
from yql_x_server.StocksQParser import parseStocksXML
from yql_x_server.YQL import YQL
from yql_x_server.Location import Location, SearchLocation
from yql_x_server.args import module_dir, args
from yql_x_server.Stocks import Symbol, getTickerChartForRange, getTickerInfo, sanitizeSymbol

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
    return re.sub('\s+(?=<)', '', xml)

def WeatherResultsFactory(q, yql: YQL, LatLongInQuery=False, Legacy=False):
    if "limit 1" in q and LatLongInQuery:
        return [Location(yql, latlong=(q['lat'], q['lon']))]
    elif "limit 1" in q:
        city = yql.getNamesForWoeidsInQ(q, nameInQuery=True)
        return [Location(yql, city_name=city[0])]
    elif LatLongInQuery:
        return [Location(yql, latlong=(q['lat'], q['lon']))]
    else:
        results = []
        cities = yql.getNamesForWoeidsInQ(q, Legacy=Legacy)
        for i in range(len(cities)):
            if LatLongInQuery:
                results.append(Location(yql, latlong=(q["lat"], q["lon"])))
            else:
                # Legacy cares about the woeid being the same as the the one in the query
                if Legacy:
                    pass # TODO
                results.append(Location(yql, city_name=cities[i], woeid=q['woeids'][i]))
        return results

def SearchResultsFactory(q, yql: YQL, Legacy=False):
    results = []
    if Legacy:
        similarResults = yql.getSimilarName(q[0], q[1])
    else:
        similarResults = yql.getSimilarName(q['term'], q['lang'])
    for similarResult in similarResults:
        results.append(SearchLocation(similarResult))
    return results

def StocksResultsFactory(q):
    results = []
    q = parseStocksXML(q)
    for symbol in q["symbols"]:
        symbol = getTickerInfo(symbol)
        if symbol:
            results.append(Symbol(symbol))
    return results
        

def XMLStocksFactoryDGW(q, reqType):
    match reqType:
        case "getquotes":
            symbols = StocksResultsFactory(q)
            xml = stocks_getquotes_template.render({
                "type": reqType,
                "timestamp": time.time(),
                "count": len(symbols),
                "symbols": symbols
            })
        case "getchart":
            _range = parseStocksXML(q)["range"]
            info: Symbol = StocksResultsFactory(q)[0]
            ticker = info.name
            pointData = getTickerChartForRange(ticker, _range)
            if not pointData:
                return "Invalid ticker or range"
            xml = stocks_getchart_template.render({
                "type": reqType,
                "timestamp": time.time(),
                "count": len(pointData),
                "symbol_name": ticker,
                "market_open": info.open,
                "market_close": info.previous_close,
                "points": pointData
            })
        case "getnews":
            posts = GetBlogPosts()
            xml = stocks_getnews_template.render({
                "count": len(posts)+1,
                "posts": posts
            })
        case "getsymbol":
            return XMLStocksFactoryDGW(q, "getquotes")
        case _:
            return "Invalid request type"
    return format_xml(xml)
   
def XMLWeatherFactoryYQL(q: dict, yql: YQL):
    if q['type'] == "search":
        xml = modern_weather_search_template.render({
            "results": SearchResultsFactory(q, yql)
        })
    elif "weather" in q['type']:
        xml = modern_weather_template.render({
            "results": WeatherResultsFactory(q, yql, True if "latlon" in q['type'] else False),
            "advert_link": args.advert_link,
            "extended_forecast_url": args.advert_link
        })
    return format_xml(xml)

# DGW is inherently legacy
def XMLWeatherFactoryDGW(q: str, yql: YQL, Search=False):
    if Search: 
        xml = legacy_weather_search_template.render({
            "results": SearchResultsFactory(q, yql)
        })
    else:
        # It's regular weather
        xml = legacy_weather_template.render({
            "results": WeatherResultsFactory(q, yql, Legacy=True),
            "advert_link": args.advert_link,
        })
    return format_xml(xml)