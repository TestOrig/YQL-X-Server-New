import sys
import os
import json
from enum import Enum
from pathlib import Path
from xml.etree import ElementTree
from fastapi import FastAPI, APIRouter, Response, Request
from fastapi.responses import PlainTextResponse
import uvicorn, sentry_sdk

from starlette_context.middleware import RawContextMiddleware
from starlette_context import context

from yql_x_server.YQL import YQL
from yql_x_server import XMLFactory
from yql_x_server.args import args

app = FastAPI()
sys.stdout.reconfigure(encoding='utf-8')

if args.sentry_url:
    sentry_sdk.init(args.sentry_url)

genPath = Path(args.generated_woeids_path)
if not os.path.exists(genPath):
    with open(genPath, "w", encoding="utf-8") as database:
        database.write(json.dumps({}))
        database.close()

yql = YQL()
yql_router = APIRouter(default_response_class=PlainTextResponse)
dgw_router = APIRouter(default_response_class=PlainTextResponse)

@dgw_router.get('/dgw')
async def dgw_get():
    return Response("ok")

@dgw_router.post('/dgw')
async def dgw(request: Request):
    body = (await request.body()).decode()
    root = ElementTree.fromstring(body)
    api = root.attrib['api']
    if api == "finance":
        req_type = root[0].attrib['type']
        return XMLFactory.xml_stocks_factory_dgw(root, req_type)
    elif api == 'weather':
        req_type = root[0].attrib['type']
        if req_type == "getlocationid":
            q = yql.parse_query(root, legacy=True)
            return XMLFactory.xml_weather_factory_dgw(q, yql, search=True)
        if req_type == "getforecastbylocationid":
            q = yql.parse_query(root, legacy=True)
            return XMLFactory.xml_weather_factory_dgw(q, yql)
    return Response("Invalid Request", status_code=400)

@yql_router.get('/v1/yql')
async def legacy_weather_yql(request: Request): 
    return await weather_endpoint(request)

@dgw_router.post('/yql/weather/dgw')
async def legacy_weather_dgw(request: Request):
    return await dgw(request)

@yql_router.get('/yql/weather')
async def weather_endpoint(request: Request):
    q = request.query_params.get('q')
    if q and q.startswith("select"):
        q = yql.parse_query(q)
        return XMLFactory.xml_weather_factory_yql(q, yql)
    return Response("Invalid Request", status_code=400)

@app.middleware("http")
def add_context(request: Request, call_next):
    context['client'] = request.client
    return call_next(request)

def start():
    app.include_router(yql_router)
    app.include_router(dgw_router)
    app.add_middleware(RawContextMiddleware)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        proxy_headers=True,
        forwarded_allow_ips='*'
    )
