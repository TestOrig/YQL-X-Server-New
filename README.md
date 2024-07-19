# WeatherX-Server
## Setup
To generate the database used with this server use ```python3 -m yql_x_server.genDatabase``` with geoplanet_places_7.10.0.tsv in your current directory.

The database is used for WOEID mapping as Yahoo's servers are gone.

## Running
Just run ```python3 -m yql_x_server``` and point your weather client to your IP:5002.

Beware, geoDatabase.json is typically around 200MB and it is loaded into RAM for performance reasons!

## Credits
@electimon I made the stupid thing

@ObscureMosquito he fixed numerous bugs I appreicate it!!!
