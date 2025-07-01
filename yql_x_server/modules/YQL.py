from .ModuleClasses import YQL
from .yql.YzuGeo import YzuGeoYQL
from .yql.YzuGeoNew import YzuGeoNewYQL

available_providers = [
    YzuGeoNewYQL,
    YzuGeoYQL
]

def get_woeid_from_name(name, lang):
    return YQL(available_providers).get_woeid_from_name(name, lang)

def get_metadata_for_woeid(woeid, lang=None):
    return YQL(available_providers).get_metadata_for_woeid(woeid, lang)

def get_similar_name(name, lang):
    return YQL(available_providers).get_similar_name(name, lang)
