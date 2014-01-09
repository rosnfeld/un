"""
Just some initial poking around with ScraperWiki data
"""

# TODO use master denormalized frame? slower but easier to follow/work with

import pandas as pd

BASE_DIR = '/home/andrew/un/ocha/dap/scraperwiki_2014-01-06/'
DATASET_CSV = BASE_DIR + 'dataset.csv'
INDICATOR_CSV = BASE_DIR + 'indicator.csv'
VALUE_CSV = BASE_DIR + 'value.csv'


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


def get_indicators_matching_units(criteria_function, excluded_indicators=set()):
    """
    Return the set of indicator IDs that match a given criteria function on the indicator units
    (but allow for manual exclusions)
    """
    all_indicators = get_indicator_frame()
    matching_indicators = all_indicators[all_indicators.units.apply(criteria_function)]
    return set(matching_indicators.index) - excluded_indicators


class BoundsReport(object):
    """
    Report on values outside the specified bounds for the specified indicators
    """
    def __init__(self, subject, indicators, lower_bound=None, upper_bound=None):
        self.subject = subject
        self.indicators = indicators
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

        all_values = get_value_frame()
        indicator_values = all_values[all_values.indID.apply(lambda x: x in self.indicators)]

        # need to convert value column, as for some indicators it can be string but for these it should be numeric
        # TODO use "is_number" column for this?
        indicator_values = indicator_values.copy()
        indicator_values.value = indicator_values.value.astype(float)

        violations_series = pd.Series(False, index=indicator_values.index)

        if self.lower_bound:
            violations_series |= indicator_values.value < self.lower_bound

        if self.upper_bound:
            violations_series |= indicator_values.value > self.upper_bound

        self.violation_values = indicator_values[violations_series]

    def __str__(self):
        output = "Bounds Report: " + self.subject + '\n'
        output += 'Indicators: ' + str(sorted(self.indicators)) + '\n'
        output += 'Bounds: (' + str(self.lower_bound) + ',' + str(self.upper_bound) + ')\n'
        output += 'Violations: ' + str(self.violation_values) + '\n\n'
        return output


def report_on_percentage_values_outside_0_to_100():
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

    indicators = get_indicators_matching_units(is_percentage_unit, excluded_indicators)

    print BoundsReport('Percentage Values', indicators, lower_bound=0, upper_bound=100)


def report_on_negative_incidence_values():
    """
    Read all indicators that are expressed in incidence terms and confirm values are not negative.
    """
    indicators = get_indicators_matching_units(is_incidence_unit)
    print BoundsReport('Incidence Values', indicators, lower_bound=0)


if __name__ == '__main__':
    report_on_percentage_values_outside_0_to_100()
    report_on_negative_incidence_values()
