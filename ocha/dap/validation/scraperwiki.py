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


def get_numeric_version(dataframe):
    # only keep the rows with numeric values, and convert them from string to float
    numeric_data = dataframe[dataframe.is_number == 1].copy()
    numeric_data.value = numeric_data.value.astype(float)
    return numeric_data


class IndicatorValueReport(object):
    """
    Check that indicator values fall within bounds prescribed in external file
    """
    def __init__(self):
        # load the data provided by ScraperWiki, and subset to the numeric-valued indicators
        data_frame = get_joined_frame()
        numeric_data = get_numeric_version(data_frame)

        # load the external file describing checks for each indicator
        checks = get_checks_frame()
        # we already have these columns in the other frame
        del checks['name']
        del checks['units']

        # join these two frames together, so upper/lower bounds are associated with values
        joined = numeric_data.join(checks, on='indID')

        # check for violations
        violations_series = pd.Series(False, index=joined.index)
        violations_series |= joined.value < joined.valueLowerBound
        violations_series |= joined.value > joined.valueUpperBound

        self.violation_values = joined[violations_series]


def get_timeseries_list(dataframe):
    """
    Takes either a values frame or a joined frame and returns a list of (many) frames, one for each
    (indID, region) pair, sorted by period.
    """
    return [group.sort('period') for key, group in dataframe.groupby(['indID', 'region'])]


class IndicatorValueChangeReport(object):
    """
    Check that changes in indicator values fall within bounds prescribed in external file
    """
    def __init__(self):
        self.load_data()
        self.load_checks()
        self.compute_violations()

    def load_data(self):
        # load the data provided by ScraperWiki, and subset to the numeric-valued indicators
        data_frame = get_joined_frame()
        numeric_data = get_numeric_version(data_frame)

        # build a timeseries for each indicator/region pair
        timeseries_list = get_timeseries_list(numeric_data)

        # take percent changes, in time. Note pct_change() is 0 to 1 scale by default, which I prefer,
        # but "percent" and the pattern already set in the data point to using a 1 to 100 scale.
        # Percentages have other warts (e.g. x +20% one year and then -20% the next year != x)
        # but alternatives probably too complicated for this project
        percent_changes = [100 * timeseries.value.pct_change() for timeseries in timeseries_list]

        # combine changes back into original numeric frame as value_pct_change column
        percent_changes_series = pd.concat(percent_changes)
        percent_changes_series.name = 'value_pct_change'
        data_with_percent_changes = numeric_data.join(percent_changes_series)

        self.data = data_with_percent_changes

    def load_checks(self):
        # load the external file describing checks for each indicator
        checks = get_checks_frame()
        # we already have these columns in the other frame
        del checks['name']
        del checks['units']

        self.checks = checks

    def compute_violations(self):
        # join data with associated bounds
        joined = self.data.join(self.checks, on='indID')

        # check for violations on absolute percentage changes
        violations_series = abs(joined.value_pct_change) > joined.percentChangeBound

        self.violation_values = joined[violations_series]


if __name__ == '__main__':
    # print IndicatorValueReport().violation_values
    print IndicatorValueChangeReport().violation_values
