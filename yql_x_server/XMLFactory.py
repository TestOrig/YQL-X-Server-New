import re
from pathlib import Path
import time
from jinja2 import Environment, FileSystemLoader
from yql_x_server.Blog import GetBlogPosts
from yql_x_server.StocksQParser import parseStocksXML
from yql_x_server.YQL import YQL
from yql_x_server.Location import Location, SearchLocation
from yql_x_server.Weather import getLatLongForQ
from yql_x_server.args import module_dir
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
        latlong = getLatLongForQ(q)
        return [Location(yql, latlong=latlong)]
    elif "limit 1" in q:
        city = yql.getNamesForWoeidsInQ(q, nameInQuery=True)
        return [Location(yql, city_name=city[0])]
    elif LatLongInQuery:
        latlong = getLatLongForQ(q)
        return [Location(yql, latlong=latlong)]
    else:
        results = []
        cities = yql.getNamesForWoeidsInQ(q, Legacy=Legacy)
        for i in range(len(cities)):
            if LatLongInQuery:
                latlong = getLatLongForQ(q)
                results.append(Location(yql, latlong=latlong))
            else:
                if Legacy:
                    # Legacy cares about the woeid being the same as the the one in the query
                    woeid = yql.getWoeidsInQuery(q, Legacy=True)[i]
                results.append(Location(yql, city_name=cities[i], woeid=woeid))
        return results

def SearchResultsFactory(q, yql: YQL):
    results = []
    similarResults = yql.getSimilarName(q)
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
   
def XMLWeatherFactoryYQL(q, yql: YQL, Legacy=False, Search=False):
    if Search:
        xml = modern_weather_search_template.render({
            "results": SearchResultsFactory(q, yql)
        })
    elif Legacy:
        xml = legacy_weather_template.render(location=WeatherResultsFactory(q, yql))
    else:
        xml = modern_weather_template.render({
            "results": WeatherResultsFactory(q, yql, True if "lat=" in q else False),
            "yahoo_mobile_url": "https://yzu.moe",
            "twc_mobile_url": "https://yzu.moe",
            "extended_forecast_url": "https://yzu.moe",
        })
    return format_xml(xml)

# DGW is inherently legacy
def XMLWeatherFactoryDGW(q, yql: YQL, Search=False):
    if Search: 
        xml = legacy_weather_search_template.render({
            "results": SearchResultsFactory(q, yql)
        })
    else:
        # It's regular weather
        xml = legacy_weather_template.render({
            "results": WeatherResultsFactory(q, yql, Legacy=True),
            "yahoo_mobile_url": "http://yzu.moe",
            "twc_mobile_url": "http://yzu.moe",
            "extended_forecast_url": "http://yzu.moe",
        })
    return format_xml(xml)