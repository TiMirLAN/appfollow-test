#!/usr/bin/env python3
# coding=utf-8

from aiohttp import web

KEYS = {'hl', 'id'}

async def load(request):
    try:
        return web.json_response(dict(
            id=request.query['id'],
            hl=request.query['hl']
        ))
    except KeyError as e:
        response = web.json_response(dict(
            error='Required param not found: {}'.format(*e.args)
        ))
        response.set_status(500)
        return response

app = web.Application()

app.add_routes([web.get('/', load)])

if __name__ == '__main__':
    web.run_app(app)
