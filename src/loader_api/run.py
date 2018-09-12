#!/usr/bin/env python3
# coding=utf-8

from asyncio import sleep
from aiohttp import web
from bs4 import BeautifulSoup
import PyChromeDevTools

GOOGLE_PLAY_URL_TEMPLATE = (
    'https://play.google.com/store/apps/details'
    '?id={id}&hl={hl}'
)
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


def get_permissiions_html(chrome):
    document = chrome.DOM.getDocument()
    body_node_id = document['result']['root']['children'][1]['children'][1]['nodeId']
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



chrome = PyChromeDevTools.ChromeInterface()
chrome.Network.enable()
chrome.Page.enable()
chrome.Runtime.enable()
chrome.DOM.enable()


async def load(request):
    for key in REQUIRED_KEYS:
        if key not in request.query:
            response = web.json_response(dict(
                error='Required param not found: {}'.format(key)
            ))
            response.set_status(500)
            return response
    chrome.Page.navigate(
        url=GOOGLE_PLAY_URL_TEMPLATE.format(**request.query)
    )
    chrome.wait_event("Page.loadEventFired", timeout=60)
    show_permissions_popup(chrome)
    # Должен быть не sleep, должно быть ожидание события перерисовки
    # или/и получения ответа от сервера.
    await sleep(2)
    permissions_html = get_permissiions_html(chrome)
    permissions_data = parse_permissions(permissions_html)
    return web.json_response(permissions_data)

app = web.Application()

app.add_routes([web.get('/', load)])

if __name__ == '__main__':
    web.run_app(app)
