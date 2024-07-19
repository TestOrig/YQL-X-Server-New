import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from yql_x_server.YQL import YQL
from yql_x_server.Location import Location, SearchLocation
from yql_x_server.Weather import getLatLongForQ
from yql_x_server.args import module_dir

templates_path = Path(module_dir) / "templates"
env = Environment(loader = FileSystemLoader(templates_path))
modern_weather_template = env.get_template('modern.jinja2')
legacy_weather_template = env.get_template('legacy.jinja2')
search_results_template = env.get_template('search.jinja2')

def ResultsFactory(q, yql: YQL, LatLongInQuery=False):
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
        cities = yql.getNamesForWoeidsInQ(q)
        for i in range(len(cities)):
            if LatLongInQuery:
                latlong = getLatLongForQ(q)
                results.append(Location(yql, latlong=latlong))
            else:
                results.append(Location(yql, city_name=cities[i]))
        return results

def SearchResultsFactory(q, yql: YQL):
    results = []
    similarResults = yql.getSimilarName(q)
    for similarResult in similarResults:
        results.append(SearchLocation(similarResult))
    return results

def XMLFactoryYQL(q, yql: YQL, Legacy=False, Search=False):
    if Search:
        xml = search_results_template.render({
            "results": SearchResultsFactory(q, yql)
        })
    elif Legacy:
        xml = legacy_weather_template.render(location=ResultsFactory(q, yql)[0])
    else:
        xml = modern_weather_template.render({
            "results": ResultsFactory(q, yql, True if "lat=" in q else False),
            "yahoo_mobile_url": "https://yzu.moe",
            "twc_mobile_url": "https://yzu.moe",
            "extended_forecast_url": "https://yzu.moe",
        })
    xml = re.sub('\s+(?=<)', '', xml)
    return xml

def XMLFactoryDGW(q, yql: YQL):
    return None