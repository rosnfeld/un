"""
This is just a quick stab to learn the FTS data and figure out how to arrange it.
The idea will be to build a local repository of all the JSON. (could be quite large)
Then in a future step I'll join that all together into reasonable "views" on the data for CKAN.
"""

import json
import urllib2

FTS_BASE_URL = "http://fts.unocha.org/api/v1/"
JSON_SUFFIX = ".json"


def fetch_json(url):
    opener = urllib2.build_opener()
    return json.load(opener.open(url))


def build_json_url(middle_part):
    return FTS_BASE_URL + middle_part + JSON_SUFFIX


def fetch_sectors_json():
    return fetch_json(build_json_url("Sector"))


def fetch_countries_json():
    return fetch_json(build_json_url("Country"))


def fetch_organizations_json():
    return fetch_json(build_json_url("Organization"))


def fetch_emergencies_json_for_country(country):
    """
    This accepts both names ("Slovakia") and ISO country codes ("SVK")
    """
    return fetch_json(build_json_url("Emergency/country/" + country))


def fetch_appeals_json_for_country(country):
    """
    This accepts both names ("Slovakia") and ISO country codes ("SVK")
    """
    return fetch_json(build_json_url("Appeal/country/" + country))
