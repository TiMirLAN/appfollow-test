#!/usr/bin/env python3
# coding=utf-8
from asyncio import sleep
from pathlib import Path
from os import environ
from urllib.request import urlopen
from aiohttp import web
from bs4 import BeautifulSoup
from socket import gethostbyname
import motor.motor_asyncio
import PyChromeDevTools

GOOGLE_PLAY_URL_TEMPLATE = (
    'https://play.google.com/store/apps/details'
    '?id={id}&hl={hl}'
)
ICONS_PATH = environ['ICONS_PATH']
CHROMIUM_HOST = environ.get('CHROMIUM_HOST', '127.0.0.1')
MONGO_HOST = environ.get('MONGO_HOST', '127.0.0.1')
# Поиск по классам ненадёжен, лучше искать по содержимому.
CLICK_EXPRESSION = """
let allLinks = document.querySelectorAll('.hrTbp');
let permissionsLink = allLinks[allLinks.length - 4];
console.log(allLinks);
console.log(permissionsLink);
permissionsLink.click();
"""
REQUIRED_KEYS = ('hl', 'id')


def show_permissions_popup(chrome):
    chrome.Runtime.evaluate(expression=CLICK_EXPRESSION)


def get_permissiions_html(chrome, body_node_id):
    permissions_node = chrome.DOM.querySelector(
        selector='[jscontroller=KkXpv][role=dialog] .fnLizd',
        nodeId=body_node_id
    )
    permissions_node_id = permissions_node['result']['nodeId']
    permissions_data = chrome.DOM.getOuterHTML(nodeId=permissions_node_id)
    return permissions_data['result']['outerHTML']


def parse_permissions(permissions_html):
    soup = BeautifulSoup(permissions_html, 'lxml')
    return [dict(
        section=div.span.getText(),
        permissions=[li.getText() for li in div.ul.children]
    ) for div in soup.find_all(class_="yk0PFc")]


def load_icon(chrome, body_node_id, app_id):
    icon_node = chrome.DOM.querySelector(
        selector='.dQrBL img',
        nodeId=body_node_id
    )
    icon_node_id = icon_node['result']['nodeId']
    icon_data = chrome.DOM.getAttributes(nodeId=icon_node_id)
    icon_attrs = icon_data['result']['attributes']
    icon_src = icon_attrs[icon_attrs.index('src') + 1]
    icon_path = Path(ICONS_PATH) / '{}.webp'.format(app_id) 
    with urlopen(icon_src) as remote, open(icon_path, 'wb') as local:
        local.write(remote.read())


chrome = PyChromeDevTools.ChromeInterface(
        host=gethostbyname('chromium'),
        port=9222
)
chrome.Network.enable()
chrome.Page.enable()
chrome.Runtime.enable()
chrome.DOM.enable()
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_HOST, 27017)

async def load(request):
    for key in REQUIRED_KEYS:
        if key not in request.query:
            response = web.json_response(dict(
                error='Required param not found: {}'.format(key)
            ))
            response.set_status(500)
            return response
    app_url = GOOGLE_PLAY_URL_TEMPLATE.format(**request.query)
    chrome.Page.navigate(url=app_url)
    chrome.wait_event("Page.loadEventFired", timeout=60)
    show_permissions_popup(chrome)
    # Должен быть не sleep, должно быть ожидание события перерисовки
    # или/и получения ответа от сервера.
    await sleep(2)
    document = chrome.DOM.getDocument()
    body_node_id = document['result']['root']['children'][1]['children'][1]['nodeId']
    permissions_html = get_permissiions_html(chrome, body_node_id)
    permissions_data = parse_permissions(permissions_html)
    load_icon(chrome, body_node_id, request.query.get('id'))
    await mongo_client.google_play.permissions.insert_one(dict(
        query=app_url[43:],
        data=permissions_data
    ))
    return web.json_response(permissions_data)

app = web.Application()

app.add_routes([web.get('/', load)])

if __name__ == '__main__':
    web.run_app(app)
