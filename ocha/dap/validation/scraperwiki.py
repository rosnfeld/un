"""
Just some initial poking around with ScraperWiki data
"""

import pandas as pd

BASE_DIR = '/home/andrew/un/ocha/dap/'
DATASET_CSV = BASE_DIR + 'dataset.csv'
INDICATOR_CSV = BASE_DIR + 'indicator.csv'
VALUE_CSV = BASE_DIR + 'value.csv'


def get_dataset_frame():
    return pd.read_csv(DATASET_CSV, index_col='dsID', parse_dates=['last_updated', 'last_scraped'])


def get_indicator_frame():
    return pd.read_csv(INDICATOR_CSV, index_col='indID')


def get_value_frame():
    return pd.read_csv(VALUE_CSV)


def check_percentages_between_0_and_100():
    """
    Read all indicators that are expressed in percentage terms and confirm values lie between 0% and 100%.
    """
    all_indicators = get_indicator_frame()

    def is_percentage_unit(unit_string):
        # TODO could definitely be improved, via regular expressions or a lot of different things

        if not isinstance(unit_string, basestring):
            return False

        if unit_string.startswith('%'):
            return True

        if unit_string.startswith('percentage'):
            return True

        return False

    percentage_indicators = all_indicators[all_indicators.units.apply(is_percentage_unit)]

    all_values = get_value_frame()
    percentage_values = all_values[all_values.indID.apply(lambda x: x in percentage_indicators.index)]

    # need to convert value column, as for some indicators it can be string but for these it should be numeric
    percentage_values = percentage_values.copy()
    percentage_values.value = percentage_values.value.astype(float)

    values_outside_range = percentage_values[(percentage_values.value < 0) | (percentage_values.value > 100)]

    return values_outside_range
