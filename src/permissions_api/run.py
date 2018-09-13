#!/usr/bin/env python3
# coding=utf-8
from asyncio import sleep
from pathlib import Path
from os import environ
from aiohttp import web, ClientSession
import motor.motor_asyncio

MONGO_HOST = environ.get('MONGO_HOST', '127.0.0.1')
# Поиск по классам ненадёжен, лучше искать по содержимому.
REQUIRED_KEYS = ('hl', 'id')

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_HOST, 27017)
QUERY = 'id={id}&hl={hl}'

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

    return web.json_response(dict(
        icon_path=permission_obj['icon_path'],
        data=permission_obj['data']
    ))

app = web.Application()

app.add_routes([web.get('/', permissions)])

if __name__ == '__main__':
    web.run_app(app)
