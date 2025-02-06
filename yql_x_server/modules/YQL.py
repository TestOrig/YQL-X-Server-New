from .ModuleClasses import YQL
from .yql.YzuGeo import YzuGeoYQL

available_providers = [
    YzuGeoYQL,
]

def get_woeid_from_name(name, lang):
    return YQL(available_providers).get_woeid_from_name(name, lang)

def get_metadata_for_woeid(woeid):
    return YQL(available_providers).get_metadata_for_woeid(woeid)

def get_similar_name(name, lang):
    return YQL(available_providers).get_similar_name(name, lang)