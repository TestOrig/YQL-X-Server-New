import json
import re
import threading
import html
from pathlib import Path
import requests
from langcodes import Language
from starlette_context import context
from ..args import args

class YQL:
    def __init__(self):
        self.gen_file_lock = threading.Lock()

    def get_woeids_in_query(self, q, formatted=False, legacy=False):
        if formatted:
            return [q] if not isinstance(q, list) else q
        woeids = []
        if legacy:
            # It's an XML document
            for item in q.iter("id"):
                woeids.append(item.text)
            return woeids
        for woeid in re.findall(r'\b\d+\b', q):
            if not woeid in woeids:
                woeids.append(woeid)
        return woeids

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
        # Generate woeid from name, store the characters in unicode int format for decoding later
        print("Generating woeid from name, " + name)
        with self.gen_file_lock:
            generated_file = open(Path(args.generated_woeids_path), "r+", encoding='utf-8')
            generated_woeids = json.load(generated_file)
            woeid = ""
            woeid_array = []
            for letter in name:
                unicode = str(ord(letter))
                woeid += unicode
                woeid_array.append(unicode)
            if not any(woeid in v for v in generated_woeids):
                print("Adding woeid to generatedWoeids.json")
                generated_woeids.update({woeid: woeid_array})
                generated_file.seek(0)
                generated_file.write(json.dumps(generated_woeids))
                generated_file.truncate()
            else:
                print("Woeid already in generatedWoeids.json")
            generated_file.close()
            return woeid

    def get_names_for_woeids(self, woeids):
        names = []
        for woeid in woeids:
            headers = {
                'User-Agent': 'YQL-X-Server',
                'X-Forwarded-For': context['client'].host
            }
            r = requests.get(
                args.yzugeo_server + "/lookup/name",
                params={"woeid": woeid},
                headers=headers,
                timeout=5
            )
            if r.status_code != 200:
                print(f"Failed to get name for {woeid}, yzugeo returned {r.status_code}")
                generated_file = open(Path(args.generated_woeids_path), "r", encoding='utf-8')
                generated_woeids = json.load(generated_file)
                if not generated_woeids:
                    generated_file.close()
                    continue
                name = ""
                for unicode_char in generated_woeids[woeid]:
                    name += chr(int(unicode_char))
                names.append(name)
                generated_file.close()
                continue
            names.append(r.json()["name"])
        return names

    def get_legacy_woeids_in_q(self, q, keep_prefix=False):
        woeids = []
        # It's an XML document
        for item in q.iter("id"):
            if "|" in item.text and not keep_prefix:
                woeids.append(item.text.split("|")[1])
            else:
                woeids.append(item.text)
        return woeids

    def get_names_for_woeids_in_q(self, q):
        return self.get_names_for_woeids(q['woeids'])

    def get_metadata_for_woeid(self, woeid):
        metadata = {}
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        r = requests.get(args.yzugeo_server + "/id/" + str(woeid), headers=headers, timeout=5)
        if r.status_code != 200:
            print(f"Failed to get metadata for {woeid}, yzugeo returned {r.status_code}")
            return {"iso": "UNKN", "state": "UNKN"}
        metadata = r.json()
        if 'detail' in metadata:
            # error case
            print(f"Error getting metadata for {woeid}: {metadata['detail']}")
            print(f"Attempted URL: {args.yzugeo_server + '/id/' + str(woeid)}")
            metadata = {"iso": "UNKN", "state": "UNKN"}
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
            timeout=5
        )
        print(f"Requesting {args.yzugeo_server + '/lookup/places'}, data: {q}")
        if r.status_code != 200:
            print(f"Failed to get similar name for {name}, yzugeo returned {r.status_code}")
            return []
        _results = r.json()
        results = [_results[key] for key in _results]
        print(f"Got similar name for {name}: {results}, len {len(results)}")
        return results

    def parse_query(self, q, legacy=False):
        if legacy:
            _type = q[0].attrib['type']
            if _type == "getlocationid":
                # search case
                result = {"term": q[0][0].text, "lang": q[0][1].text, "type": "search"}
                print(f"Parsing query: {q}, result: {result}")
                return result
            result = {}
            result['woeids'] = self.get_legacy_woeids_in_q(q)
            result['raw_woeids'] = self.get_legacy_woeids_in_q(q, keep_prefix=True)
            result['type'] = "weather/woeid"
            result['lang'] = q[0][1].text
            print(f"Parsing query: {q}, result: {result}")
            return result
        q = html.unescape(q)
        result = {'lang': re.search(r"lang='([^']+)'", q).group(1)}
        if 'partner.weather.locations' in q and not 'yql.query.multi' in q:
            result['term'] = re.search(r'query="([^"]+)"', q).group(1)
            result['type'] = "search"
        elif "lat=" in q and "lon=" in q:
            result['lat'] = re.search(r'lat=(-?\d+\.\d+)', q).group(1)
            result['lon'] = re.search(r'lon=(-?\d+\.\d+)', q).group(1)
            result['type'] = "weather/latlon"
        elif "woeid" in q:
            result['woeids'] = list(set(re.findall(r'woeid=(\d+)', q)))
            if not result['woeids']:
                result['woeids'] = list(set(re.findall(r'woeid.*?(\d+)', q)))
            result['type'] = "weather/woeid"
        result['lang'] = re.search(r"lang='([^']+)'", q).group(1)
        print(f"Parsing query: {q}, result: {result}")
        return result
