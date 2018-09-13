#!/usr/bin/env python3
# coding=utf-8
from asyncio import sleep
from pathlib import Path
from os import environ, path
from aiohttp import web, ClientSession
import aiohttp_jinja2
import jinja2
import motor.motor_asyncio

ICONS_PATH = environ['ICONS_PATH']
MONGO_HOST = environ.get('MONGO_HOST', '127.0.0.1')
REQUIRED_KEYS = ('hl', 'id')
QUERY = 'id={id}&hl={hl}'
TEMPLATES_PATH = path.join(
    path.dirname(path.realpath(__file__)),
    'templates'
)

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_HOST, 27017)

@aiohttp_jinja2.template('index.jinja2')
async def permissions(request):
    for key in REQUIRED_KEYS:
        if key not in request.query:
            response = web.json_response(dict(
                error='Required param not found: {}'.format(key)
            ))
            response.set_status(500)
            return response
    query = QUERY.format(**request.query)
    permission_obj = await mongo_client.google_play.permissions.find_one(
        filter=dict(query={'$eq':query}),
    )
    if not permission_obj:
        async with ClientSession() as session:
            async with session.get('http://loader:8080/?{}'.format(query)) as resp:
                resp_data = await resp.json()
                if resp.reason != 'OK':
                    return web.json_response(dict(
                        error= 'Loader api returns error: {error}'.format(
                            **resp_data
                        )
                    ))
                permission_obj = resp_data

    return dict(
        icon_path=permission_obj['icon_path'],
        data=permission_obj['data']
    )

app = web.Application()

app.add_routes([web.get('/', permissions)])
aiohttp_jinja2.setup(
    app,
    loader=jinja2.FileSystemLoader(TEMPLATES_PATH)
)
app.add_routes([web.static('/icons', ICONS_PATH)])
if __name__ == '__main__':
    web.run_app(app)
