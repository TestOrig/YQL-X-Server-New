import sys
import os
import json
from pathlib import Path
from xml.etree import ElementTree
from fastapi import FastAPI, APIRouter, Response, Request
from fastapi.responses import PlainTextResponse
import uvicorn
from yql_x_server.YQL import YQL
from yql_x_server.StocksQParser import *
from yql_x_server.XMLFactory import XMLFactoryYQL
from yql_x_server.args import args

app = FastAPI()
sys.stdout.reconfigure(encoding='utf-8')

genPath = Path(args.generated_woeids_path)
if not os.path.exists(genPath):
    with open(genPath, "w") as database:
        database.write(json.dumps({}))
        database.close()

yql = YQL()

yql_router = APIRouter()
dgw_router = APIRouter()

# Stocks
@dgw_router.get('/dgw')
async def dgw():
    print("Legacy app found!")
    return Response("ok")

@dgw_router.post('/dgw')
async def dgw(request: Request):
    body = await request.body()
    root = ElementTree.fromstring(body)
    type = root[0].attrib['type']
    api = root.attrib['api']
    if api == "finance":
        q = parseQuery(body)
        return XMLGenerator.getStocksXMLWithQandType(q, type)
    if api == "finance":
        print("Using finance")
        q = parseQuery(body)
        return XMLGenerator.getStocksXMLWithQandType(q, type)
    elif api == 'weather':
        print("Using Weather")
        return legacyWeatherDGW(request)

# Weather

# iOS 5 seems to use this endpoint, let's redirect to the regular function
@yql_router.get('/v1/yql')
def legacyWeatherYQL(request: Request): 
    print("Legacy app found!")
    return weatherEndpoint(request)

@yql_router.post('/yql/weather/dgw')
async def legacyWeatherDGW(request: Request):
    print("Legacy app found!")
    print("To be implmeneted")
    return Response("ok")

# iOS 6 contacts this endpoint for all things weather
@yql_router.get('/yql/weather', response_class=PlainTextResponse)
async def weatherEndpoint(request: Request):
    q = request.query_params.get('q')
    if q:
        if 'partner.weather.locations' and not 'yql.query.multi' in q:
            q = q[q.index('query="')+7:q.index('" a')]
            return XMLFactoryYQL(q, yql, Search=True)
        elif 'partner.weather.forecasts' in q:
            return XMLFactoryYQL(q, yql)
    return Response("Invalid Request", status_code=400)

def start():
    app.include_router(yql_router)
    app.include_router(dgw_router)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port
    )
