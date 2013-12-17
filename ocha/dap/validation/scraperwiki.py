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


def is_percentage_unit(unit_string):
    """
    Returns a set of indicator IDs that have percentage units
    """
    # TODO could definitely be improved, via regular expressions or a lot of different things

    if not isinstance(unit_string, basestring):
        return False

    if '%' in unit_string:
        return True

    if 'percentage' in unit_string:
        return True

    return False


def is_incidence_unit(unit_string):
    """
    Returns a set of indicator IDs that are measured by some sort of "count"
    (e.g. #people affected by disasters)
    """
    # TODO could definitely be improved

    if not isinstance(unit_string, basestring):
        return False

    if unit_string in ('uno', 'count', 'thousands', 'millions'):
        return True

    if ' per ' in unit_string:  # one could argue this is its own category
        return True

    return False


def get_indicators_matching_units(criteria_function):
    """
    Return the set of indicator IDs that match a given criteria function on the indicator units
    """
    all_indicators = get_indicator_frame()
    matching_indicators = all_indicators[all_indicators.units.apply(criteria_function)]
    return set(matching_indicators.index)


def find_values_out_of_bounds(units_criteria_function, excluded_indicators=None, lower_bound=None, upper_bound=None):
    """
    Return all indicators that match the criteria function (but allow for manual exclusions),
    and return those that are outside the specified bounds
    """
    all_values = get_value_frame()
    indicators = get_indicators_matching_units(units_criteria_function)

    if excluded_indicators:
        indicators -= excluded_indicators

    indicator_values = all_values[all_values.indID.apply(lambda x: x in indicators)]

    # need to convert value column, as for some indicators it can be string but for these it should be numeric
    # TODO use "is_number" column for this?
    indicator_values = indicator_values.copy()
    indicator_values.value = indicator_values.value.astype(float)

    violations_series = pd.Series(False, index=indicator_values.index)

    if lower_bound:
        violations_series |= indicator_values.value < lower_bound

    if upper_bound:
        violations_series |= indicator_values.value > upper_bound

    return indicator_values[violations_series]


def find_percentage_values_outside_0_to_100():
    """
    Read all indicators that are expressed in percentage terms and confirm values lie between 0% and 100%.
    """
    # some percentages are okay to be outside the range
    excluded_indicators = {
        'PSP050',  # population growth rate
        'PSP060',  # population growth rate, again
        'PVE120',  # education enrollment vs theoretical baseline
        'PSE150',  # age dependency ratio
        'PSE200',  # consumer price inflation
    }

    return find_values_out_of_bounds(is_percentage_unit, excluded_indicators, lower_bound=0, upper_bound=100)


def find_negative_incidence_values():
    """
    Read all indicators that are expressed in incidence terms and confirm values are not negative.
    """

    return find_values_out_of_bounds(is_incidence_unit, lower_bound=0)


if __name__ == "__main__":
    print "Percentage Values outside 0% to 100%:"
    print find_percentage_values_outside_0_to_100()
    print
    print "Incidence Values below 0:"
    print find_negative_incidence_values()


# TODO restructure this to print clearly which indicators are being tested, with what criteria
