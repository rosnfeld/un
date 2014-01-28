"""
Just some initial poking around with ScraperWiki data
"""

import pandas as pd
import numpy as np
import os

BASE_DIR = os.environ.get('SCRAPERWIKI_DATA_DIR')
DATASET_CSV = BASE_DIR + 'dataset.csv'
INDICATOR_CSV = BASE_DIR + 'indicator.csv'
VALUE_CSV = BASE_DIR + 'value.csv'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# maybe put the CSV in some sort of 'resources' subdir?
CHECKS_CSV = os.path.join(SCRIPT_DIR, 'indicator_checks.csv')


def get_dataset_frame():
    return pd.read_csv(DATASET_CSV, index_col='dsID', parse_dates=['last_updated', 'last_scraped'])


def get_indicator_frame():
    return pd.read_csv(INDICATOR_CSV, index_col='indID')


def get_value_frame():
    return pd.read_csv(VALUE_CSV, low_memory=False)


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


def standardize_period(period_value):
    """
    An attempt at converting the period column into something more workable
    """
    if '/' in period_value:
        # remove frequency indicator after the slash
        slash_index = period_value.find('/')
        period_value = period_value[:slash_index]

    if len(period_value) == 4:
        # assume end of year
        period_value += '-12-31'

    return pd.datetools.parse(period_value)


class GapTimesReport(object):
    """
    Reports on gaps in time series
    """
    def __init__(self):
        data_frame = get_joined_frame()
        data_frame['period_end'] = data_frame.period.apply(standardize_period)

        # build a timeseries for each indicator/region pair
        timeseries_list = get_timeseries_list(data_frame)

        deviations = []

        for timeseries in timeseries_list:
            date_diffs = timeseries.period_end.diff()

            # leap-year hack: convert 366 day differences to 365 day differences
            date_diffs[date_diffs == np.timedelta64(366, 'D')] = np.timedelta64(365, 'D')

            # a little unusual that it's a series, but there can be a tie for most frequent
            mode_series = date_diffs.mode()

            if mode_series.empty:
                continue

            deviation_rows = timeseries[date_diffs != mode_series[0]]

            if not deviation_rows.empty:
                deviations.append(deviation_rows)

        self.violation_values = pd.concat(deviations)


class CorrelationReport(object):
    """
    Reports on correlations between various indicators.
    Creates region-date pairs as the "key" on which to align different indicators.
    """
    def __init__(self):
        # load the data provided by ScraperWiki, and subset to the numeric-valued indicators
        data_frame = get_joined_frame()
        numeric_data = get_numeric_version(data_frame)
        numeric_data['period_end'] = numeric_data.period.apply(standardize_period)

        # build a matrix that has 'region' and 'period_end' as the 2-level index,
        # a column for each value of 'indID',
        # and values as per the 'value' column
        # (yes, this looks like some pandas voodoo)
        indicator_per_column = numeric_data.set_index(['region', 'period_end', 'indID']).value.unstack()

        # now compute the column-vs-column (indID vs indID) correlation matrix
        # This will use region-period_end pairs as the 'keys' for alignment,
        # and only use the data where both indicators "align"
        # TODO should add a "count" criterion here and throw out correlations based on say, < 20 samples
        self.indicator_correlations = indicator_per_column.corr()

        # another format for the data: a Series with (ind1, ind2) in the index and correlation as the value
        ind_corr_series = self.indicator_correlations.unstack()

        self.perfectly_correlated_pairs = []

        for (ind1, ind2), correlation in ind_corr_series.iteritems():
            if correlation > 0.999 and ind2 > ind1:
                self.perfectly_correlated_pairs.append((ind1, ind2))


class CoverageSummaryReport(object):
    """
    For each indicator, captures the count of countries/regions with at least data point,
    and the earliest and latest dates with at least one data point.
    """
    def __init__(self):
        data_frame = get_joined_frame()
        data_frame['period_end'] = data_frame.period.apply(standardize_period)

        groupby_key = ['indID', 'ind_name']

        region_counts = data_frame.groupby(groupby_key).apply(lambda x: len(x.region.unique()))
        period_min = data_frame.groupby(groupby_key).period_end.min().astype('datetime64[ns]')
        period_max = data_frame.groupby(groupby_key).period_end.max().astype('datetime64[ns]')

        self.summary_frame = pd.DataFrame({'region_count': region_counts,
                                           'period_min': period_min, 'period_max': period_max})


if __name__ == '__main__':
    # print IndicatorValueReport().violation_values
    # print IndicatorValueChangeReport().violation_values
    print GapTimesReport().violation_values
