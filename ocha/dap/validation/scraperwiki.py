"""
Just some initial poking around with ScraperWiki data
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
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
    """
    Only keep the rows with numeric values, and convert them from string to float
    """
    numeric_data = dataframe[dataframe.is_number == 1].copy()
    numeric_data.value = numeric_data.value.astype(float)
    return numeric_data


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


def get_timeseries_list(dataframe):
    """
    Takes either a values frame or a joined frame and returns a list of (many) frames, one for each
    (indID, region) pair, sorted by period.
    """
    return [group.sort('period') for key, group in dataframe.groupby(['indID', 'region'])]


def plot_indicator_timeseries_for_region(dataframe, ind_id, region):
    """
    Generates a simple matplotlib plot of the value timeseries for the given indicator/region
    """
    raw_rows = dataframe[(dataframe.indID == ind_id) & (dataframe.region == region)]

    if raw_rows.empty:
        print 'No data for ' + ind_id + ' and ' + region
        return

    # assume these transformations have not yet been done, should be cheap on a single indicator/region
    numeric = get_numeric_version(raw_rows)
    numeric['period_end'] = numeric.period.apply(standardize_period)

    timeseries = numeric.set_index('period_end')

    ind = get_indicator_frame()
    ind_units = ind.units[ind_id]

    title = ind_id + ' for ' + region

    fig = plt.figure()
    timeseries.value.plot()
    plt.title(title)
    plt.ylabel(ind_units)

    return fig


def plot_indicator_heatmap(dataframe, ind_id):
    """
    Generates a "heatmap" type image that is useful for spotting the presence of outliers.
    However, at present it's a little tricky to _identify_ the actual outlier values.
    """
    ind_subset = dataframe[dataframe.indID == ind_id]

    # assume these transformations have not yet been done, should be cheap on a single indicator
    ind_subset = get_numeric_version(ind_subset)
    ind_subset['period_end'] = ind_subset.period.apply(standardize_period)

    # create a matrix of values arranged by region columns and period rows (index)
    # pandas handles the timeseries index nicely, but for plotting with imshow we'll want to transpose this
    ind_crosssection = ind_subset.set_index(['period_end', 'region']).value.unstack()

    fig = plt.figure()
    axes = plt.gca()

    time_ticks = mpl.dates.date2num(ind_crosssection.index)
    extent = [time_ticks[0], time_ticks[-1], 0, len(ind_crosssection.columns)]

    # plot that matrix, assigning colors based on where values sit in the overall range
    plt.imshow(ind_crosssection.T, extent=extent, interpolation='none', aspect='auto', origin='lower')

    # this tells matplotlib to interpret the x values as datetimes
    axes.xaxis_date(tz=ind_crosssection.index.tz)

    regions = ind_crosssection.columns.tolist()
    axes.yaxis.set_major_locator(mpl.ticker.LinearLocator())
    axes.yaxis.set_major_formatter(mpl.ticker.IndexFormatter(regions))

    ind = get_indicator_frame()
    ind_name = ind.name[ind_id]
    plt.title(ind_id + ": " + ind_name)

    # add a "legend" that explains how the colors map to values
    plt.colorbar()

    return fig


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
        self.indicator_correlations = indicator_per_column.corr(min_periods=20)

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


class CVReport(object):
    """
    For each indicator, looks at the stability of the coefficient of variation (CV) across regions, across time.
    (I am not yet sure how I feel about this test, but Javier is interested in it)
    """
    def __init__(self):
        values = get_value_frame()
        numeric_data = get_numeric_version(values)

        grouped = numeric_data.groupby('indID')

        def calculate_cv_stats(indicator_group):
            # further group by period, then calculate coefficient of variation (across regions) for each period
            by_period = indicator_group.groupby('period')
            cv_per_period = by_period.value.std() / by_period.value.mean()

            # then, take the mean and standard deviation of the timeseries of CV values
            return pd.Series([cv_per_period.mean(), cv_per_period.std()], index=['cv_mean', 'cv_std'])

        self.summary_frame = grouped.apply(calculate_cv_stats)


class ValueTypeReport(object):
    """
    Check that indicator values conform to a specified type
    """
    def __init__(self):
        # load the data provided by ScraperWiki
        data_frame = get_joined_frame()

        # load the external file describing checks for each indicator
        checks = get_checks_frame()
        # we already have these columns in the other frame
        del checks['name']
        del checks['units']

        # join these two frames together, so value_types are associated with values
        joined = data_frame.join(checks, on='indID')

        # check for int violations
        int_rows = joined[joined.value_type == 'int']

        # parse strings into floats
        int_values = int_rows.value.astype(float)

        # do a simple type-conversion check for now
        # a better check might be to use some sort of "epsilon" threshold
        self.int_violations = int_rows[int_values.astype(int) != int_values]

        # at some point we could do validation on string values also, like checking that URLs are properly formed


class IsNumberReport(object):
    """
    Check that the "is_number" column is correct
    """
    def __init__(self):
        data_frame = get_value_frame()
        # try to convert to numeric type - this method won't raise errors, instead will just write NaNs where it fails
        value_as_number = data_frame.value.convert_objects(convert_numeric=True)
        conversion_success_series = ~value_as_number.isnull()

        mismatch_series = (data_frame.is_number == 1) != conversion_success_series

        self.violation_values = data_frame[mismatch_series]


if __name__ == '__main__':
    # print IndicatorValueReport().violation_values
    # print IndicatorValueChangeReport().violation_values
    # print GapTimesReport().violation_values
    # print CorrelationReport().perfectly_correlated_pairs
    # print ValueTypeReport().int_violations
    # print IsNumberReport().violation_values.indID.value_counts()
    plot_indicator_timeseries_for_region(get_value_frame(), 'PVH150', 'SDN')
    plt.show()
