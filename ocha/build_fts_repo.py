"""
This is just a quick stab to learn the FTS data and figure out how to arrange it.
The idea will be to build a local repository of all the JSON as pandas data. (could be quite large)
Then in a future step I'll join that all together into reasonable "views" on the data for CKAN.
"""

import pandas as pd

FTS_BASE_URL = 'http://fts.unocha.org/api/v1/'
JSON_SUFFIX = '.json'


def fetch_json_as_dataframe(url):
    return pd.read_json(url)


def fetch_json_as_dataframe_with_id(url):
    return fetch_json_as_dataframe(url).set_index('id')


def build_json_url(middle_part):
    return FTS_BASE_URL + middle_part + JSON_SUFFIX


def fetch_sectors_json_as_dataframe():
    return fetch_json_as_dataframe_with_id(build_json_url('Sector'))


def fetch_countries_json_as_dataframe():
    return fetch_json_as_dataframe_with_id(build_json_url('Country'))


def fetch_organizations_json_as_dataframe():
    return fetch_json_as_dataframe_with_id(build_json_url('Organization'))


def fetch_emergencies_json_for_country_as_dataframe(country):
    """
    This accepts both names ("Slovakia") and ISO country codes ("SVK")
    """
    return fetch_json_as_dataframe_with_id(build_json_url('Emergency/country/' + country))


def fetch_appeals_json_for_country_as_dataframe(country):
    """
    This accepts both names ("Slovakia") and ISO country codes ("SVK")
    """
    return fetch_json_as_dataframe_with_id(build_json_url('Appeal/country/' + country))


def fetch_projects_json_for_appeal_as_dataframe(appeal_id):
    return fetch_json_as_dataframe_with_id(build_json_url('Project/appeal/' + str(appeal_id)))


def fetch_clusters_json_for_appeal_as_dataframe(appeal_id):
    # NOTE no id present in this data
    return fetch_json_as_dataframe(build_json_url('Cluster/appeal/' + str(appeal_id)))


def fetch_contribution_json_for_appeal_as_dataframe(appeal_id):
    return fetch_json_as_dataframe_with_id(build_json_url('Contribution/appeal/' + str(appeal_id)))


def fetch_funding_json_for_appeal_as_dataframe(appeal_id):
    # NOTE no id present in this data, and it parses a bit weird
    # TODO improve parsing
    return fetch_json_as_dataframe(build_json_url('funding') + '?Appeal=' + str(appeal_id))


def fetch_pledges_json_for_appeal_as_dataframe(appeal_id):
    # NOTE no id present in this data, and it parses a bit weird
    # TODO improve parsing
    return fetch_json_as_dataframe(build_json_url('pledges') + '?Appeal=' + str(appeal_id))
