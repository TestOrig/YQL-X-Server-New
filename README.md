# YQL-X-Server
## Introduction
As you may or may not know, the Weather and Stocks services on earlier iOS versions (3-7) were provided by Yahoo. Ever since Yahoo's public YQL API was deprecated and thus removed, these apps have been long since broken. Broken until now that is, this project aims to create a replacement server implementing these APIs to restore functionality to these apps.

Currently there are the following Weather providers
1. YzuWeather (Electimon's free to use weather provider)
2. OpenWeatherMap (via the use of an API key provided in arguments)

By default the server will use OpenWeatherMap ONLY when an API key is provided
in all other cases it will utilize Electimon's weather provider.

As of right now, I (Electimon) and Requis (@ObscureMosquito) host public instances, if you wish to use those, just install the WeatherX tweak via Cydia on either of our repos, they are listed below.

* http://yzu.moe/dev
* http://cydia.skyglow.es

## Warning
This project is in active development by me (Electimon), and as such, is subject breakage at any time, sorry not sorry :)

## Running
To run this server you need [uv](https://github.com/astral-sh/uv) installed.
After installing uv, run ```uv run yql_x_server``` and point your weather client to your IP:8000.

## Settings
Please run the above command with --help to see available arguments.

## Credits
@electimon I made the stupid thing

@ObscureMosquito he fixed numerous bugs I appreicate it!!!
