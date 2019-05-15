#!/usr/bin/python3

"""
get_category_items.py
MediaWiki Action API Code Samples
Demo of `Categorymembers` module: List twenty items in a category.
MIT license
"""

import requests

S = requests.Session()

URL = "https://commons.wikimedia.org/w/api.php?"


def get_category_items(category):
    PARAMS = {
        'action': "query",
        'list': "categorymembers",
        'cmtitle': category,
        'cmlimit': 2,
        'cmtype': "file",
        'prop': "images",
        'format': "json"
    }
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    return DATA
