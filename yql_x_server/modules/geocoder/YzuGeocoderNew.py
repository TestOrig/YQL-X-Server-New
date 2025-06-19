import requests
from geopy.location import Location
from starlette_context import context
from ...args import args

class YzuGeocoderNew:
    def __init__(self):
        pass

    def geocode(self, name, country=None):
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        url = args.yzugeo_server + f"/lookup/search?text={name}&lang={country}&placetype=region,county,locality,neighborhood"
        print(f"Geocoding {name}, url: {url}")
        r = requests.get(url, timeout=5, headers=headers)
        if r.status_code != 200 or "[]" in r.text:
            raise ValueError(f"Geocoding failed for {name}, status code: {r.status_code}")
        data = r.json()
        if not data or len(data) == 0:
            raise ValueError(f"No results found for {name}, response: {data}")
        data = data[0]
        geom = data.get("geom")
        if not geom:
            raise ValueError(f"No geometry found for {name}, response: {data}")
        lat = geom["lat"]
        lon = geom["lon"]
        return Location("", (lat, lon), data)

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
