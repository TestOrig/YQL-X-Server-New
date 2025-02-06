import json
import requests
from langcodes import Language
from starlette_context import context
from ...args import args
from ...utils import gen_woeid_for_name, get_gen_name_for_woeid
from ..ModuleClasses import YQL

class YzuGeoYQL(YQL):
    def get_woeid_from_name(self, name, lang):
        if not name:
            print("Name is empty")
            return "000000"
        print("Getting woeid from name, " + name)
        result = self.get_similar_name(name, lang)
        if result:
            result = result[0]['woeid']
            print("Woeid from name is " + result)
            return result
        return gen_woeid_for_name(name)

    def get_metadata_error(self, woeid):
        name = get_gen_name_for_woeid(woeid)
        return {
            "id": woeid,
            "name": name,
            "iso": "UNKN",
            "state": ""
        }

    def get_metadata_for_woeid(self, woeid):
        metadata = {}
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        r = requests.get(args.yzugeo_server + "/id/" + str(woeid), headers=headers)
        if r.status_code != 200:
            print(f"Failed to get metadata for {woeid}, yzugeo returned {r.status_code}")
            return self.get_metadata_error(woeid)
        metadata = r.json()
        if 'detail' in metadata:
            # error case
            print(f"Error getting metadata for {woeid}: {metadata['detail']}")
            print(f"Attempted URL: {args.yzugeo_server + '/id/' + str(woeid)}")
            return self.get_metadata_error(woeid)
        return metadata

    def get_similar_name(self, name, lang):
        q = {
            "query": name,
            "limit": 10,
            "alt_response": True,
            "place_type_id": [12, 8, 7, 22, 9],
            "language": Language.get(lang).to_alpha3().upper()
        }
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        r = requests.post(args.yzugeo_server + "/lookup/places",
            data=json.dumps(q),
            headers=headers,
        )
        print(f"Requesting {args.yzugeo_server + '/lookup/places'}, data: {q}")
        if r.status_code != 200 or "No results found" in r.text:
            print(f"Failed to get similar name for {name}, yzugeo returned {r.status_code}")
            return []
        _results = r.json()
        results = [_results[key] for key in _results]
        print(f"Got similar name for {name}: {results}, len {len(results)}")
        return results
