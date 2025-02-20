class Weather:
    def get_weather(self, lat, lng):
        for provider in self.available_providers:
            try:
                weather = provider().get_weather_dict(lat, lng)
                if weather:
                    print(f"Utilizing weather from provider: {provider.__name__}")
                    return weather
            except Exception as e:
                print(f"Error getting weather from {provider.__name__}: {e}")
                if self.available_providers.index(provider) == len(self.available_providers) - 1:
                    raise e
                continue
        return None

    def __init__(self, providers=None):
        self.days = []
        self.hours = []
        self.available_providers = providers

    def get_weather_dict(self, lat, lng):
        pass # This method should return a dict containing the following as an example.
        # {
        #     "barometer": 1013,
        #     "currently_condition_code": 800,
        #     "currently_condition_text": "Clear",
        #     "current_time_12h": "12:00 PM",
        #     "current_time_24h": "12:00",
        #     "days": [{
        #         "ordinal": 0,
        #         "currently_condition_code": 800,
        #         "currently_condition_text": "Clear",
        #         "high": 25.0,
        #         "high_rounded": 25,
        #         "low": 10.0,
        #         "low_rounded": 10,
        #         "pop": 0
        #     }],
        #     "dew_point": 10.0,
        #     "feels_like": 25.0,
        #     "hours": [{
        #         "currently_condition_code": 800,
        #         "poP": 0,
        #         "temp": 25.0,
        #         "time_24h": "12:00"
        #     }],
        #     "moonfacevisible": 0,
        #     "moonphase": 0.5,
        #     "p_humidity": 80,
        #     "sunrise_12h": "6:00 AM",
        #     "sunrise_24h": "06:00",
        #     "sunset_12h": "6:00 PM",
        #     "sunset_24h": "18:00",
        #     "temp": 25.0,
        #     "temp_rounded": 25,
        #     "timezone": "+08:00",
        #     "visibility": 10.0,
        #     "wind_chill": 25.0,
        #     "wind_deg": 180,
        #     "wind_speed": 5.0
        # }

class YQL:
    def __init__(self, providers=[]):
        self.available_providers = providers
    
    def get_woeid_from_name(self, name, lang):
        """
        This method should return a WOEID for the given name to the best of its ability.
        """
        for provider in self.available_providers:
            try:
                woeid = provider().get_woeid_from_name(name, lang)
                print(f"Utilizing WOEID from provider: {provider.__name__}")
                return woeid
            except Exception as e:
                print(f"Error getting WOEID from {provider.__name__}: {e}")
                if self.available_providers.index(provider) == len(self.available_providers) - 1:
                    raise e
                continue
        return None
    
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
        for provider in self.available_providers:
            try:
                metadata = provider().get_metadata_for_woeid(woeid)
                print(f"Utilizing metadata from provider: {provider.__name__}")
                return metadata
            except Exception as e:
                print(f"Error getting metadata from {provider.__name__}: {e}")
                if self.available_providers.index(provider) == len(self.available_providers) - 1:
                    raise e
                continue
        return None
    
    def get_similar_name(self, name, lang):
        """
        This method should return a list in the format of:
        [
            {
                "name": NAME,
                "woeid": WOEID,
                "iso": "ISO"
            }
        ]
        """
        for provider in self.available_providers:
            try:
                similar_names = provider().get_similar_name(name, lang)
                print(f"Utilizing similar names from provider: {provider.__name__}")
                return similar_names
            except Exception as e:
                print(f"Error getting similar names from {provider.__name__}: {e}")
                if self.available_providers.index(provider) == len(self.available_providers) - 1:
                    raise e
                continue
        return None
