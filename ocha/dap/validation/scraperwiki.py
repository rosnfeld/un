"""
Just some initial poking around with ScraperWiki data
"""

import pandas as pd

BASE_DIR = '/home/andrew/un/ocha/dap/scraperwiki_2013-12-13/'
DATASET_CSV = BASE_DIR + 'dataset.csv'
INDICATOR_CSV = BASE_DIR + 'indicator.csv'
VALUE_CSV = BASE_DIR + 'value.csv'


def get_dataset_frame():
    return pd.read_csv(DATASET_CSV, index_col='dsID', parse_dates=['last_updated', 'last_scraped'])


def get_indicator_frame():
    return pd.read_csv(INDICATOR_CSV, index_col='indID')


def get_value_frame():
    return pd.read_csv(VALUE_CSV)


def get_percentage_indicators():
    """
    Returns a set of indicator IDs that have percentage units
    """
    all_indicators = get_indicator_frame()

    def is_percentage_unit(unit_string):
        # TODO could definitely be improved, via regular expressions or a lot of different things

        if not isinstance(unit_string, basestring):
            return False

        if '%' in unit_string:
            return True

        if 'percentage' in unit_string:
            return True

        return False

    percentage_indicators = all_indicators[all_indicators.units.apply(is_percentage_unit)]
    return set(percentage_indicators.index)


def find_percentage_values_outside_0_to_100():
    """
    Read all indicators that are expressed in percentage terms and confirm values lie between 0% and 100%.
    Yes, many indicators may naturally not be in this range, but this is just
    """
    all_values = get_value_frame()
    percentage_indicators = get_percentage_indicators()

    # some percentages are okay to be outside the range:
    # PSP050, PSP060 - population growth rate
    # PSE150 - age dependency ratio
    # PSE200 - consumer price inflation
    excluded_indicators = {'PSP050', 'PSP060', 'PSE150', 'PSE200'}

    percentage_indicators = percentage_indicators - excluded_indicators

    percentage_values = all_values[all_values.indID.apply(lambda x: x in percentage_indicators)]

    # need to convert value column, as for some indicators it can be string but for these it should be numeric
    # TODO use "is_number" column for this?
    percentage_values = percentage_values.copy()
    percentage_values.value = percentage_values.value.astype(float)

    values_outside_range = percentage_values[(percentage_values.value < 0) | (percentage_values.value > 100)]

    return values_outside_range


if __name__ == "__main__":
    print "Percentage Values outside 0% to 100%:"
    print find_percentage_values_outside_0_to_100()
