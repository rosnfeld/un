"""
An "deep dive" of exploratory data analysis (EDA) on a few countries in the ScraperWiki data.

This doesn't particularly belong in "validation" but it's related to scraperwiki.py.

Things to do:
- look at cross-section of indicators for a given region, do indicators from different sources "line up"/relate?

"""
import scraperwiki
import os
import matplotlib.pyplot as plt
import datetime
import textwrap
import matplotlib_utils

REGIONS_OF_INTEREST = ['COL', 'KEN']
NEIGHBORS = {
    'COL': ['BRA', 'ECU', 'PAN', 'PER', 'VEN'],
    'KEN': ['ETH', 'SDN', 'SOM', 'SSD', 'TZA', 'UGA']
}

ANALYSIS_START_DATE = datetime.date(1990, 1, 1)


def build_analysis_matrix(region):
    joined = scraperwiki.get_joined_frame()
    numeric = scraperwiki.get_numeric_version(joined)

    regions = [region] + NEIGHBORS[region]
    filtered = numeric[numeric.region.apply(lambda x: x in regions)]

    scraperwiki.add_standardized_period(filtered)
    filtered = filtered[filtered.period_end > ANALYSIS_START_DATE]

    return filtered


def plot_indicator_timeseries_for_region(dataframe, ind_id, ds_id, region, comparison_regions=None):
    """
    Generates a simple matplotlib plot of the value timeseries for the given indicator/dataset/region
    """
    raw_rows = dataframe[(dataframe.indID == ind_id) & (dataframe.dsID == ds_id) & (dataframe.region == region)]

    if raw_rows.empty:
        print 'No data for %s/%s/%s' % (ind_id, ds_id, region)
        return None

    legend = False

    if comparison_regions:
        regions = [region] + comparison_regions
        region_filter = lambda x: x in regions
        raw_rows = dataframe[(dataframe.indID == ind_id) & (dataframe.dsID == ds_id) &
                             dataframe.region.apply(region_filter)]
        legend = True

    # assume these transformations have not yet been done, should be cheap on a single indicator/region
    numeric = scraperwiki.get_numeric_version(raw_rows)
    scraperwiki.add_standardized_period(numeric)

    timeseries = numeric.set_index('period_end')

    ind = scraperwiki.get_indicator_frame()
    ind_name = ind.name[ind_id]
    ind_units = ind.units[ind_id]

    # indicator names can be very long, so wrap them if necessary
    title = ind_id + "\n" + textwrap.fill(ind_name, width=80)

    fig = plt.figure()

    # TODO: use saturated color for "main" region and less saturated color (or lower alpha) for comparison regions
    # maybe also list main region 1st
    timeseries.groupby('region').value.plot(legend=legend)
    plt.title(title, fontsize=11)

    if isinstance(ind_units, basestring):
        plt.ylabel(ind_units)

    matplotlib_utils.prettyplotlib_style(fig)

    return fig


if __name__ == '__main__':
    # save off indicator series plots for all numeric indicators for regions of interest

    for region in REGIONS_OF_INTEREST:
        dataframe = build_analysis_matrix(region)
        neighbors = NEIGHBORS[region]

        dir_path = os.path.join('/tmp/deep_dive', region)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        for i, row in dataframe[['indID', 'dsID']].drop_duplicates().iterrows():
            ind_id = row['indID']
            ds_id = row['dsID']
            figure = plot_indicator_timeseries_for_region(dataframe, ind_id, ds_id, region, neighbors)

            if not figure:
                continue

            filename = ind_id.replace('/', '_') + '_' + ds_id + '.png'
            file_path = os.path.join(dir_path, filename)
            print 'Writing', file_path
            figure.savefig(file_path)
            plt.close(figure)
