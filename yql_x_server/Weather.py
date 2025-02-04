from cachetools import TTLCache

class Weather:
    available_providers = [
        "YzuWeather",
        "OWMWeather",
    ]

    @staticmethod
    def get_weather(lat, lng):
        for provider in Weather.available_providers:
            from importlib import import_module
            provider = getattr(import_module(f"yql_x_server.{provider}"), provider)()
            try:
                weather = provider.get_current_weather(lat, lng)
                days = provider.get_days()
                hours = provider.get_hours()
                if weather and days and hours:
                    print(f"Utilizing weather from provider: {provider.__class__.__name__}")
                    return weather, days, hours
            except Exception as e:
                print(f"Error getting weather from {provider.__class__.__name__}: {e}")
                continue
        return None

    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=3600)
        self.days = []
        self.hours = []
    
    def store(self, data, key):
        self.cache[key] = data

    def retrieve(self, key):
        return self.cache.get(key)

    def get_current_weather(self, lat, lng):
        pass # This method should return a dict containing the following as an example.
        # {
        #     "barometer": 1013,
        #     "currently_condition_code": 800,
        #     "currently_condition_text": "Clear",
        #     "current_time_12h": "12:00 PM",
        #     "current_time_24h": "12:00",
        #     "dew_point": 10.0,
        #     "feels_like": 25.0,
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
        # } consider using store and retrieve at the start and end of this method

    def get_days(self):
        pass # This method should return a list of Day objects
    
    def get_hours(self):
        pass # This method should return a list of Hour objects

    class Day:
        def __init__(self, idx, data):
            self.ordinal = idx # this is to order the days in the app

            self.currently_condition_code = data["currently_condition_code"]
            self.currently_condition_text = data["currently_condition_text"]
            self.high = data["high"]
            self.high_rounded = data["high_rounded"]
            self.low = data["low"]
            self.low_rounded = data["low_rounded"]
            self.pop = data["pop"]

    class Hour:
        def __init__(self, data): # no ordinal here since days have a fixed number of hours
            self.currently_condition_code = data["currently_condition_code"]
            self.poP = data["poP"]
            self.temp = data["temp"]
            self.time_24h = data["time_24h"]




