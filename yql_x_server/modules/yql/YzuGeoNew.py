import requests
from langcodes import Language
from starlette_context import context
from ...args import args
from ..ModuleClasses import YQL

class YzuGeoNewYQL(YQL):
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
        raise ValueError(f"Could not find WOEID for name: {name}")

    def _transform_metadata_response(self, raw: dict, woeid: str) -> dict:
        data = raw.get(str(woeid), {})
        if not data:
            raise ValueError(f"No metadata found for WOEID: {woeid}")

        iso = data.get("abbr", "UNKN")
        if iso == "UNKN":
            lineage = data.get("lineage", [])
            if lineage and isinstance(lineage[0], dict):
                country_id = lineage[0].get("country_id")
                if country_id:
                    country_data = self.get_metadata_for_woeid(country_id)
                    iso = country_data.get("iso", "UNKN")

        return {
            "id": woeid,
            "name": data.get("name", ""),
            "iso": iso,
            "state": ""
        }


    def get_metadata_for_woeid(self, woeid):
        """
        This method should return a dict in the form of:
        {
            "id": woeid,
            "name": NAME,
            "iso": "ISO",
            "state": "STATE"
        }
        """
        metadata = {}
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        url = args.yzugeo_server + f"/lookup/id?ids={str(woeid)}"
        r = requests.get(url, headers=headers)
        print(f"Requesting metadata for {woeid}, URL: {url}")
        if r.status_code != 200:
            raise ValueError(f"Failed to get metadata for {woeid}, yzugeo returned {r.status_code}")
        metadata = r.json()
        if not metadata:
            raise ValueError(f"No metadata found for WOEID: {woeid}")
        return self._transform_metadata_response(metadata, woeid)
    
    def _transform_search_response(self, response: list) -> list:
        results = []
        for item in response:
            iso = "UNKN"
            for lineage in item.get("lineage", [{}])[0]:
                if lineage == "country":
                    iso = item["lineage"][0][lineage].get("abbr", "UNKN")
                    break
            result = {
                "name": item.get("name", ""),
                "woeid": item.get("id", ""),
                "iso": iso
            }
            if not result["name"] or not result["woeid"]:
                print(f"Skipping invalid result: {result}")
                continue
            results.append(result)
        if len(results) > 15:
            results = results[:15]
        return results

    def get_similar_name(self, name, lang):
        headers = {
            'User-Agent': 'YQL-X-Server',
            'X-Forwarded-For': context['client'].host
        }
        url = args.yzugeo_server + f"/lookup/search?mode=live&text={name}&lang={Language.get(lang).to_alpha3()}&placetype=region,county,locality,neighborhood"
        r = requests.get(url, timeout=5, headers=headers)
        print(f"Requesting similar name for {name} with lang {lang}, URL: {url}")
        if r.status_code != 200 or "[]" in r.text:
            print(f"Failed to get similar name for {name}, yzugeo returned {r.status_code}")
            return []
        results = self._transform_search_response(r.json())
        print(f"Got similar name for {name}: {results}, len {len(results)}")
        return results
