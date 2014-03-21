"""
An "deep dive" of exploratory data analysis (EDA) on a few countries in the ScraperWiki data.

This doesn't particularly belong in "validation" but it's related to scraperwiki.py.

Things to do:
- look at cross-section of indicators for a given region, do indicators from different sources "line up"/relate?

"""
import scraperwiki
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import datetime
import textwrap
import matplotlib_utils

REGIONS_OF_INTEREST = ['COL', 'KEN', 'YEM']
NEIGHBORS = {
    'COL': ['BRA', 'ECU', 'PAN', 'PER', 'VEN'],
    'KEN': ['ETH', 'SDN', 'SOM', 'SSD', 'TZA', 'UGA'],
    'YEM': ['OMN', 'SAU']
}
REFERENCE_REGIONS = ['SWE', 'AFG']

ANALYSIS_START_DATE = datetime.date(1990, 1, 1)
ANALYSIS_END_DATE = datetime.date(2012, 12, 31)

INDICATORS_TO_EXCLUDE = {
    '_Land area (sq. km)',  # not really interesting for this analysis
    '_Access to electricity (% of population)',  # insufficient history
    'PCH090',  # insufficient history
    'PCH090',  # insufficient history
    'PCX130',  # insufficient history
    'PSE220',  # insufficient history
    'PVL010',  # insufficient history
    'PVX010',  # insufficient history
    'PVX020',  # insufficient history
    '_Fixed-telephone subscriptions per 100 inhabitants',  # duplicate of another indicator
    '_Internet users per 100 inhabitants',  # duplicate of another indicator
    '_Mobile-cellular subscriptions per 100 inhabitants',  # duplicate of another indicator
    '_Population, total',  # duplicate of another indicator
}

TECH_INDICATORS = {
    'PCX090',
    'PCX100',
    'PCX110',
}

MORTALITY_RATIO_INDICATORS = {
    'PVH120',
    'PVH140',
    'PVH180',
    'PVH190',
}

AGE_INDICATORS = {
    'PSE140',
    'PSE150',
    'PSP070',
    'PVH010',
}

FOOD_WATER_INDICATORS = {
    'PVN010',  # will pull in 2 sources
    'PVN050',
    'PVW010',
    '_Population undernourished, percentage',
    'PVF020',
}


def build_analysis_matrix(region, comparison_regions):
    joined = scraperwiki.get_joined_frame()
    numeric = scraperwiki.get_numeric_version(joined)

    regions = [region] + comparison_regions
    filtered = numeric[numeric.region.apply(lambda x: x in regions)]

    scraperwiki.add_standardized_period(filtered)
    filtered = filtered[filtered.period_end > ANALYSIS_START_DATE]

    return filtered


def plot_indicator_timeseries_for_region(axes, dataframe, ind_id, ds_id, region, comparison_regions):
    """
    Generates a simple matplotlib plot of the value timeseries for the given indicator/dataset/region
    """
    raw_rows = dataframe[(dataframe.indID == ind_id) & (dataframe.dsID == ds_id) & (dataframe.region == region)]

    if raw_rows.empty:
        print 'No data for %s/%s/%s' % (ind_id, ds_id, region)
        return False

    if comparison_regions:
        regions = [region] + comparison_regions
        region_filter = lambda x: x in regions
        raw_rows = dataframe[(dataframe.indID == ind_id) & (dataframe.dsID == ds_id) &
                             dataframe.region.apply(region_filter)]

    ind = scraperwiki.get_indicator_frame()
    ind_name = ind.name[ind_id]
    ind_units = ind.units[ind_id]

    ds = scraperwiki.get_dataset_frame()
    ds_name = ds.name[ds_id]

    # indicator names can be very long, so wrap them if necessary
    ind_name_wrapped = textwrap.fill(ind_name, width=80)

    # we really only have 3 lines for title, so don't use a newline if the wrap consumed one
    ds_join = '\n' if '\n' not in ind_name_wrapped else ' / '

    title = ind_id + '\n' + ind_name_wrapped + ds_join + ds_name

    axes.set_color_cycle(matplotlib_utils.REFERENCE_PALETTE_RGB)

    pivoted = raw_rows.pivot('period_end', 'region', 'value')
    pivoted.index = pd.to_datetime(pivoted.index)
    # this is a little gross as creates the impression of us having more data than we actually do
    pivoted = pivoted.interpolate(method='time')

    pivoted[region].plot(ax=axes, label=region)

    if comparison_regions:
        other_regions_pivot = pivoted[pivoted.columns - [region]]
        if not other_regions_pivot.empty:
            other_regions_pivot.plot(ax=axes, alpha=0.8)

    axes.set_title(title, fontsize=11)
    axes.set_xlabel('')
    if isinstance(ind_units, basestring):
        axes.set_ylabel(ind_units)

    axes.set_xlim((ANALYSIS_START_DATE, ANALYSIS_END_DATE))
    # for some reason this doesn't work nicely
    # plt.xticks(list(pd.date_range(ANALYSIS_START_DATE, ANALYSIS_END_DATE, freq='a')))
    plt.gcf().autofmt_xdate(rotation=0, ha='center', bottom=0.1)

    matplotlib_utils.prettyplotlib_style(axes)

    return True


def plot_indicators_for_region(base_path, region, indicators):
    """
    Save off indicator series plots for numeric indicators for region and reference regions
    """
    # comparison_regions = NEIGHBORS[region]
    comparison_regions = REFERENCE_REGIONS
    dataframe = build_analysis_matrix(region, comparison_regions)
    dir_path = os.path.join(base_path, region)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    for i, row in dataframe[['indID', 'dsID']].drop_duplicates().iterrows():
        ind_id = row['indID']
        ds_id = row['dsID']

        if ind_id not in indicators:
            continue

        figure = plt.figure()
        axes = plt.gca()
        success = plot_indicator_timeseries_for_region(axes, dataframe, ind_id, ds_id, region, comparison_regions)

        if not success:
            continue

        filename = ind_id.replace('/', '_') + '_' + ds_id + '.png'
        file_path = os.path.join(dir_path, filename)
        print 'Writing', file_path
        figure.savefig(file_path)
        plt.close(figure)


def plot_indicators_for_region_combined(base_path, region, indicators, title):
    """
    Write multiple indicators to a single plot, with aligned x-axis
    """
    comparison_regions = REFERENCE_REGIONS
    dataframe = build_analysis_matrix(region, comparison_regions)
    dir_path = os.path.join(base_path, region)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    ds_ind_pairs = []

    for i, row in dataframe[['indID', 'dsID']].drop_duplicates().iterrows():
        ind_id = row['indID']
        ds_id = row['dsID']

        if ind_id not in indicators:
            continue

        ds_ind_pairs.append((ds_id, ind_id))

    pairs_length = len(ds_ind_pairs)

    figure = plt.figure()

    for i, (ds_id, ind_id) in enumerate(ds_ind_pairs):
        axes = plt.subplot(pairs_length, 1, i + 1)
        plot_indicator_timeseries_for_region(axes, dataframe, ind_id, ds_id, region, comparison_regions)
        axes.set_title(axes.get_title().replace('\n', ' / '))

    title += ' - ' + region

    plt.suptitle(title, fontsize=(mpl.rcParams['font.size'] + 2))
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)

    filename = title + '.png'
    file_path = os.path.join(dir_path, filename)
    print 'Writing', file_path
    figure.savefig(file_path)
    plt.close(figure)


def custom_plot_tech_indicators(base_path):
    """
    Write tech indicators to a single plot, with aligned x-axis
    """
    regions = REGIONS_OF_INTEREST + REFERENCE_REGIONS
    dataframe = build_analysis_matrix([], regions)
    dir_path = os.path.join(base_path, 'cross_region')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    ds_ind_pairs = [('World Bank', 'PCX090'), ('World Bank', 'PCX110'), ('World Bank', 'PCX100')]
    ind = scraperwiki.get_indicator_frame()

    figure = plt.figure()
    mpl.rc('font', size=11)

    for i, (ds_id, ind_id) in enumerate(ds_ind_pairs):
        axes = plt.subplot(3, 1, i + 1)

        ind_name = ind.name[ind_id]
        ind_units = ind.units[ind_id]

        ind_rows = dataframe[(dataframe.indID == ind_id) & (dataframe.dsID == ds_id)]

        ds = scraperwiki.get_dataset_frame()
        ds_name = ds.name[ds_id]

        title = ind_id + ' / ' + ind_name + ' / ' + ds_name

        # axes.set_color_cycle(matplotlib_utils.REFERENCE_PALETTE_RGB)

        pivoted = ind_rows.pivot('period_end', 'region', 'value')
        pivoted.index = pd.to_datetime(pivoted.index)
        # this is a little gross as creates the impression of us having more data than we actually do
        pivoted = pivoted.interpolate(method='time')

        pivoted.plot(ax=axes, alpha=0.8)

        axes.set_title(title)
        axes.set_xlabel('')
        if isinstance(ind_units, basestring):
            axes.set_ylabel(ind_units)

        axes.set_xlim((ANALYSIS_START_DATE, ANALYSIS_END_DATE))
        matplotlib_utils.prettyplotlib_style(axes)

        axes.legend(loc='best', frameon=False, fontsize=10)

    plt.gcf().autofmt_xdate(rotation=0, ha='center', bottom=0.1)
    plt.tight_layout()

    filename = 'tech_plot.png'
    file_path = os.path.join(dir_path, filename)
    print 'Writing', file_path
    figure.savefig(file_path)
    plt.close(figure)


if __name__ == '__main__':
    # all indicators
    ind = scraperwiki.get_indicator_frame()
    indicators = set(ind.index) - INDICATORS_TO_EXCLUDE
    # for region_of_interest in REGIONS_OF_INTEREST:
    #     plot_indicators_for_region('/tmp/deep_dive', region_of_interest, indicators)

    # tech indicators
    # for region_of_interest in REGIONS_OF_INTEREST:
    #     plot_indicators_for_region('/tmp/deep_dive/tech/', region_of_interest, TECH_INDICATORS)

    # custom_plot_tech_indicators('/tmp/deep_dive/tech/')

    # age
    # for region_of_interest in REGIONS_OF_INTEREST:
    #     plot_indicators_for_region('/tmp/deep_dive/age/', region_of_interest, AGE_INDICATORS)

    # food_water
    # for region_of_interest in REGIONS_OF_INTEREST:
    #     plot_indicators_for_region('/tmp/deep_dive/food_water/', region_of_interest, FOOD_WATER_INDICATORS)

    mpl.rc('font', size=8)
    for region_of_interest in REGIONS_OF_INTEREST:
        base_path = '/tmp/deep_dive/'

        # this looks pretty good, as is
        plot_indicators_for_region_combined(base_path, region_of_interest, TECH_INDICATORS, 'Technology Adoption')

        ind_with_2_sources = {'PVN010'}
        # TODO would probably be better with both sources on the same axes? i.e. more custom plotting
        plot_indicators_for_region_combined(base_path, region_of_interest, ind_with_2_sources, 'Cross-Source Comparison')

        plot_indicators_for_region_combined(base_path, region_of_interest, FOOD_WATER_INDICATORS - ind_with_2_sources, 'Food and Water')

        plot_indicators_for_region_combined(base_path, region_of_interest, MORTALITY_RATIO_INDICATORS, 'Mortality')
        plot_indicators_for_region_combined(base_path, region_of_interest, AGE_INDICATORS, 'Aging')
