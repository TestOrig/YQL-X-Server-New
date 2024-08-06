import json
import re
import threading
import requests
import html
from langcodes import Language
from pathlib import Path
from yql_x_server.args import args

class YQL:
    def __init__(self):
        self.generatedFileLock = threading.Lock()

    def getWoeidsInQuery(self, q, formatted=False, Legacy=False):
        if formatted:
            return [q] if not isinstance(q, list) else q
        woeids = []
        if Legacy:
            # It's an XML document
            for item in q.iter("id"):
                woeids.append(item.text)
            return woeids
        for woeid in re.findall(r'\b\d+\b', q):
            if not woeid in woeids:
                woeids.append(woeid)
        return woeids
    
    def getWoeidFromName(self, name, lang):
        if not name:
            print("Name is empty")
            return "000000"
        print("Getting woeid from name, " + name)
        try:
            result = self.getSimilarName(name, lang)[0]['woeid']
            print("Woeid from name is " + result)
            return result
        except:
            # Generate woeid from name, store the characters in unicode int format for decoding later
            print("Generating woeid from name, " + name)
            with self.generatedFileLock:
                generatedFile = open(Path(args.generated_woeids_path), "r+")
                generatedWoeids = json.load(generatedFile)
                woeid = ""
                woeidArray = []
                for letter in name:
                    unicode = str(ord(letter))
                    woeid += unicode
                    woeidArray.append(unicode)
                if not any(woeid in v for v in generatedWoeids):
                    print("Adding woeid to generatedWoeids.json")
                    generatedWoeids.update({woeid: woeidArray})
                    generatedFile.seek(0)
                    generatedFile.write(json.dumps(generatedWoeids))
                    generatedFile.truncate()
                else:
                    print("Woeid already in generatedWoeids.json")
                generatedFile.close()
                return woeid

    def getNamesForWoeids(self, woeids):
        names = []
        
        for woeid in woeids:
            try:
                r = requests.get(args.yzugeo_server + "/lookup/name", params={"woeid": woeid})
                if r.status_code != 200:
                    print(f"Failed to get name for {woeid}, yzugeo returned {r.status_code}")
                    continue
                names.append(r.json()["name"])
            except Exception as e:
                generatedFile = open(Path(args.generated_woeids_path), "r")
                generatedWoeids = json.load(generatedFile)
                if not generatedWoeids:
                    continue
                name = ""
                for unicodeChar in generatedWoeids[woeid]:
                    name += chr(int(unicodeChar))
                names.append(name)
        return names

    def getNamesForWoeidsInQ(self, q, formatted=False, Legacy=False):
        if Legacy:
            woeids = []
            # It's an XML document
            for item in q.iter("id"):
                if "|" in item.text:
                    woeids.append(item.text.split("|")[1])
                else:
                    woeids.append(item.text)
            return self.getNamesForWoeids(woeids)
        return self.getNamesForWoeids(q['woeids'])

    def getSimilarName(self, name, lang):
        q = {
            "query": name,
            "limit": 10,
            "alt_response": True,
            "place_type_id": [12, 8, 7, 22, 9],
            "language": Language.get(lang).to_alpha3().upper()
        }
        print(json.dumps(q))
        r = requests.post(args.yzugeo_server + "/lookup/places", data=json.dumps(q))
        if r.status_code != 200:
            print(f"Failed to get similar name for {name}, yzugeo returned {r.status_code}")
            return []
        _results = r.json()
        results = [_results[key] for key in _results]
        print(f"Got similar name for {name}: {results}")
        return results

    def parseQuery(self, q):            
        q = html.unescape(q)
        result = {'lang': re.search(r"lang='([^']+)'", q).group(1)}
        print(f"Parsing query: {q}")
        if 'partner.weather.locations' and not 'yql.query.multi' in q:
            result['term'] = re.search(r'query="([^"]+)"', q).group(1)
            result['type'] = "search"
        elif "lat=" in q and "lon=" in q:
            result['lat'] = re.search(r'lat=(-?\d+\.\d+)', q).group(1)
            result['lon'] = re.search(r'lon=(-?\d+\.\d+)', q).group(1)
            result['type'] = "weather/latlon"
        elif "woeid" in q:
            result['woeids'] = re.findall(r'\(woeid=(\d+)\)', q)
            result['type'] = "weather/woeid"
        
        return result

        