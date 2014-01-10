"""
Just some initial poking around with ScraperWiki data
"""

import pandas as pd

BASE_DIR = '/home/andrew/un/ocha/dap/scraperwiki_2014-01-06/'
DATASET_CSV = BASE_DIR + 'dataset.csv'
INDICATOR_CSV = BASE_DIR + 'indicator.csv'
VALUE_CSV = BASE_DIR + 'value.csv'

# TODO figure out how to load a file based on relative location to script, put this into some sort of "resources" dir
CHECKS_CSV = '/home/andrew/git/un/ocha/dap/validation/indicator_checks.csv'


def get_dataset_frame():
    return pd.read_csv(DATASET_CSV, index_col='dsID', parse_dates=['last_updated', 'last_scraped'])


def get_indicator_frame():
    return pd.read_csv(INDICATOR_CSV, index_col='indID')


def get_value_frame():
    return pd.read_csv(VALUE_CSV)


def get_joined_frame():
    """
    Combine the dataset/indicator/value frames into one master frame.
    Resulting columns are:
    dsID - the dataset ID
    region - seems to mostly be ISO country codes, though maybe not always
    indID - the indicator ID
    period - the time period in question, can be a date, a year, or year/P?Y where ? encodes the period
        (e.g. every 5 years is P5Y)
    value - string containing the indicator value
    is_number - whether to interpret the value as a number
    source - URL where the original data can be found
    ds_last_updated - last time the dataset was updated (what does updated mean in this context?)
    ds_last_scraped - last time the dataset was scraped
    ds_name - the dataset name
    ind_name - the indicator name
    ind_units - the indicator units (these could use some more standardization)
    """
    ds = get_dataset_frame()
    ds = ds.rename(columns=lambda x: "ds_" + x)

    ind = get_indicator_frame()
    ind = ind.rename(columns=lambda x: "ind_" + x)

    val = get_value_frame()

    return val.join(ds, on='dsID').join(ind, on='indID')


def get_checks_frame():
    return pd.read_csv(CHECKS_CSV, index_col='indID')


class IndicatorValueReport(object):
    """
    Check that indicator values fall within bounds prescribed in external file
    """
    def __init__(self):
        # load the data provided by ScraperWiki
        data_frame = get_joined_frame()
        # only keep the rows with numeric values, and convert them from string to float
        numeric_data = data_frame[data_frame.is_number == 1].copy()
        numeric_data.value = numeric_data.value.astype(float)

        # load the external file describing checks for each indicator
        checks = get_checks_frame()
        # we already have these columns in the other frame
        del checks['name']
        del checks['units']

        # join these two frames together, so upper/lower bounds are associated with values
        joined = numeric_data.join(checks, on='indID')

        # check for violations
        violations_series = pd.Series(False, index=joined.index)
        violations_series |= joined.value < joined.lowerBound
        violations_series |= joined.value > joined.upperBound

        self.violation_values = joined[violations_series]


if __name__ == '__main__':
    print IndicatorValueReport().violation_values
