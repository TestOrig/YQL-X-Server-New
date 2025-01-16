import requests
from geopy.location import Location
from yql_x_server.args import args
from starlette_context import context

class YzuGeocoder:
    def __init__(self):
        pass

    def geocode(self, name):
        url = f"{args.yzugeo_server}/geocode?name={name}"
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        response = requests.get(url, headers=headers)
        if not response.ok:
            return None, None
        data = response.json()
        loc = Location("", (data['lat'], data['lon']), data)
        return loc

    def reverse(self, latlong: tuple):
        url = f"{args.yzugeo_server}/reverse_geocode?lat={latlong[0]}&lon={latlong[1]}"
        print(f"Reverse geocoding {latlong[0]}, {latlong[1]}, url: {url}")
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        response = requests.get(url, headers=headers)
        if not response.ok:
            return None
        res = response.json()
        loc = Location(res['name'], (latlong[0], latlong[1]), res)
        return loc