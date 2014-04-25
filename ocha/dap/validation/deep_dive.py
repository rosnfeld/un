"""
An "deep dive" of exploratory data analysis (EDA) on a few countries in the ScraperWiki data.

This doesn't particularly belong in "validation" but it's related to scraperwiki.py.

Unfortunately a bit of a messy scratch-pad more than anything.
"""
import scraperwiki
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import datetime
import textwrap
import matplotlib_utils
import fts_queries

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

MORTALITY_RATIO_INDICATORS = [
    'PVH120',
    # 'PVH140',  # seems to be obsolete
    'PVH180',
    # 'PVH190',  # seems to be obsolete
]

AGE_INDICATORS = {
    'PSE140',
    'PSE150',
    'PSP070',
    'PVH010',
}

FOOD_WATER_INDICATORS = {
    # 'PVN010',  # will pull in 2 sources, handled separately
    # 'PVN050',  # spotty data
    'PVW010',
    '_Population undernourished, percentage',
    'PVF020',
}

REGION_COLOR = (0.2, 0.2, 0.7, 1.0)  # dark blue

REFERENCE_REGION_COLORMAP = {
    'AFG': (0.7, 0.2, 0.7, 0.8),  # purple
    'SWE': (0.2, 0.7, 0.7, 0.8),  # cyan
}


class CountryFundingCacheByYear(object):
    """
    Caches total funding amounts for each country by year
    """
    def __init__(self):
        self.year_cache = {}

        self.country_iso_code_to_name = {}
        countries = fts_queries.fetch_countries_json_as_dataframe()
        for country_id, row in countries.iterrows():
            self.country_iso_code_to_name[row['iso_code_A']] = row['name']

    def get_total_country_funding_for_year(self, country_code, year):
        if year not in self.year_cache:
            funding_by_country =\
                fts_queries.fetch_grouping_type_json_for_year_as_dataframe('funding', year, 'country', 'country')

            self.year_cache[year] = funding_by_country

        # possibly no funding at all in that year
        funding_series = self.year_cache[year]
        if funding_series.empty:
            return 0

        country_name = self.country_iso_code_to_name[country_code]

        if country_name in funding_series.funding:
            return funding_series.funding.loc[country_name]
        else:
            return 0


COUNTRY_FUNDING_CACHE = CountryFundingCacheByYear()


def build_analysis_matrix(region, comparison_regions):
    joined = scraperwiki.get_joined_frame()
    numeric = scraperwiki.get_numeric_version(joined)

    regions = [region] + comparison_regions
    filtered = numeric[numeric.region.apply(lambda x: x in regions)]

    scraperwiki.add_standardized_period(filtered)
    filtered = filtered[filtered.period_end > ANALYSIS_START_DATE]

    return filtered


def write_figure_to_file(figure, dir_path, filename):
    file_path = os.path.join(dir_path, filename)
    print 'Writing', file_path

    figure.set_size_inches(8.8, 6.6)

    figure.savefig(file_path)
    plt.close(figure)


def format_currency_millions(value, position):
    millions = value/1e6
    return '{:,.0f}'.format(millions)


def plot_indicator_timeseries_for_region(axes, dataframe, ind_id, ds_id, region, comparison_regions, show_trend=False):
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

    pivoted[region].plot(ax=axes, label=region, color=REGION_COLOR)

    if show_trend:
        linear_model = pd.ols(y=pivoted[region], x=pivoted.index.to_series().astype(int), intercept=True)
        year_ends = pd.date_range(ANALYSIS_START_DATE, ANALYSIS_END_DATE, freq='A')
        annual_trend = linear_model.predict(x=year_ends.to_series().astype(int))
        label = region + ' Trend'
        annual_trend.plot(ax=axes, color=matplotlib_utils.MEDIUM_GRAY, alpha=0.7, linestyle='--', label=label)

    if comparison_regions:
        other_regions_pivot = pivoted[pivoted.columns - [region]]
        if not other_regions_pivot.empty:
            for other_region in other_regions_pivot.columns:
                pivoted[other_region].plot(ax=axes, color=REFERENCE_REGION_COLORMAP[other_region])

    axes.set_title(title, fontsize=11)
    axes.set_xlabel('')
    if isinstance(ind_units, basestring):
        axes.set_ylabel(ind_units)

    axes.set_xlim((ANALYSIS_START_DATE, ANALYSIS_END_DATE))
    # for some reason this doesn't work nicely
    # plt.xticks(list(pd.date_range(ANALYSIS_START_DATE, ANALYSIS_END_DATE, freq='a')))
    plt.gcf().autofmt_xdate(rotation=0, ha='center', bottom=0.1)

    matplotlib_utils.prettyplotlib_style(axes)
    # matplotlib_utils.wolfram_style(axes)

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
        write_figure_to_file(figure, dir_path, filename)


def plot_indicators_for_region_combined(base_path, region, indicators, title):
    """
    Write multiple indicators to a single plot, with aligned x-axis
    """
    mpl.rcdefaults()  # reset matplotlib settings
    mpl.rc('font', size=8)  # annoying you can't "push"/"pop" context (I guess I could always add that...)

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

    matplotlib_utils.add_figure_legend(figure)

    plt.suptitle(title, fontsize=(mpl.rcParams['font.size'] + 2))
    plt.tight_layout()
    plt.subplots_adjust(top=0.9, bottom=0.09)

    filename = title + '.png'
    write_figure_to_file(figure, dir_path, filename)


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
    mpl.rcdefaults()  # reset matplotlib settings
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
    write_figure_to_file(figure, dir_path, filename)


def custom_plot_PVN010_different_sources(base_path, region):
    """
    Write PVN010 from 2 sources to a single plot
    """
    dataframe = build_analysis_matrix(region, [])
    dir_path = os.path.join(base_path, region)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    ind_id = 'PVN010'

    figure = plt.figure()
    mpl.rcdefaults()  # reset matplotlib settings
    mpl.rc('font', size=11)

    axes = plt.gca()

    raw_rows = dataframe[(dataframe.indID == ind_id) & (dataframe.region == region)]

    ind = scraperwiki.get_indicator_frame()
    ind_name = ind.name[ind_id]
    ind_units = ind.units[ind_id]

    title = ind_id + ' / ' + ind_name + ' - ' + region + '\n' + 'Compared Across Data Sources'

    pivoted = raw_rows.pivot('period_end', 'ds_name', 'value')
    pivoted.index = pd.to_datetime(pivoted.index)
    # this is a little gross as creates the impression of us having more data than we actually do
    pivoted = pivoted.interpolate(method='time')

    pivoted.plot(ax=axes)

    axes.set_title(title, fontsize=11)
    axes.set_xlabel('')
    if isinstance(ind_units, basestring):
        axes.set_ylabel(ind_units)

    axes.set_xlim((ANALYSIS_START_DATE, ANALYSIS_END_DATE))
    plt.gcf().autofmt_xdate(rotation=0, ha='center', bottom=0.1)

    matplotlib_utils.prettyplotlib_style(axes, include_legend=True)

    filename = 'PVN010_different_sources - ' + region + '.png'
    write_figure_to_file(figure, dir_path, filename)


def plot_fts_funding_over_time(base_path, region):
    dir_path = os.path.join(base_path, region)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    funding_per_year = {}
    for year in range(ANALYSIS_START_DATE.year, ANALYSIS_END_DATE.year + 1):
        funding_per_year[year] = COUNTRY_FUNDING_CACHE.get_total_country_funding_for_year(region, year)


    figure = plt.figure()
    mpl.rcdefaults()  # reset matplotlib settings
    mpl.rc('font', size=11)

    axes = plt.gca()

    pd.Series(funding_per_year).plot(ax=axes)

    matplotlib_utils.prettyplotlib_style(axes)

    axes.set_xlabel('')  # for consistency with other plots

    axes.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(format_currency_millions))
    axes.set_ylabel('USD Millions')

    title = "Funding as recorded by FTS - " + region
    axes.set_title(title, fontsize=11)

    plt.tight_layout()

    filename = 'FTS_funding - ' + region + '.png'
    write_figure_to_file(figure, dir_path, filename)


def get_fts_appeal_ids_for_year(region, year):
    appeals = fts_queries.fetch_appeals_json_for_country_as_dataframe(region)
    appeals_in_year = appeals[appeals.year == year]
    return appeals_in_year.index.values


def plot_fts_cluster_funding(base_path, region, year):
    """
    Make a horizontal bar chart of FTS funding by cluster.
    FTS reports cluster funding by appeal, and a country can have 0-n appeals per year.
    For now, combine funding across appeals for a given year.
    """
    mpl.rcdefaults()  # reset matplotlib settings
    mpl.rc('font', size=9)  # annoying you can't "push"/"pop" context (I guess I could always add that...)

    dir_path = os.path.join(base_path, region)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    appeal_ids = get_fts_appeal_ids_for_year(region, year)

    cluster_data_list = [fts_queries.fetch_clusters_json_for_appeal_as_dataframe(appeal_id) for appeal_id in appeal_ids]

    if not cluster_data_list:
        return

    # collapse appeals for a given year
    concat_cluster_data = pd.concat(cluster_data_list)
    funding_by_cluster = concat_cluster_data.groupby('name').funding.sum()

    # sort by amount
    funding_by_cluster.sort()

    # TODO standardize the cluster names across years

    figure = plt.figure()
    axes = plt.gca()

    funding_by_cluster.plot(ax=axes, kind='barh', color=matplotlib_utils.MEDIUM_GRAY, edgecolor='none')

    matplotlib_utils.prettyplotlib_style(axes)
    axes.yaxis.set_ticks_position('none')

    axes.set_ylabel('')
    axes.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(format_currency_millions))
    axes.set_xlabel('USD Millions')

    title = 'FTS funding by cluster - ' + region + ' ' + str(year)
    plt.suptitle(title, fontsize=11)

    plt.tight_layout()
    plt.subplots_adjust(top=0.95)

    filename = title + '.png'
    write_figure_to_file(figure, dir_path, filename)


def plot_heatmap_per_indicator(dir_path):
    """
    Save off heatmaps for all numeric indicators
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    mpl.rcdefaults()  # reset matplotlib settings

    joined = scraperwiki.get_joined_frame()
    numeric = scraperwiki.get_numeric_version(joined)

    for i, row in numeric[['indID', 'dsID']].drop_duplicates().iterrows():
        ind_id = row['indID']
        ds_id = row['dsID']

        if ind_id.startswith('_'):  # only use proper indicators
            continue

        # require at least a little history for display
        ind_subset = numeric[(numeric.indID == ind_id) & (numeric.dsID == ds_id)]
        if len(ind_subset.period.unique()) <= 1:
            continue

        figure = scraperwiki.plot_indicator_heatmap(numeric, ind_id, ds_id)

        filename = ind_id.replace('/', '_') + '_' + ds_id + '.png'
        write_figure_to_file(figure, dir_path, filename)


if __name__ == '__main__':

    for region_of_interest in REGIONS_OF_INTEREST:
        base_path = '/tmp/deep_dive/country_plots/'

        plot_indicators_for_region_combined(base_path, region_of_interest, TECH_INDICATORS, 'Technology Adoption')
        plot_indicators_for_region_combined(base_path, region_of_interest, FOOD_WATER_INDICATORS, 'Food and Water')
        plot_indicators_for_region_combined(base_path, region_of_interest, MORTALITY_RATIO_INDICATORS, 'Mortality')
        plot_indicators_for_region_combined(base_path, region_of_interest, AGE_INDICATORS, 'Aging')

        custom_plot_PVN010_different_sources(base_path, region_of_interest)

        plot_fts_cluster_funding(base_path, region_of_interest, ANALYSIS_END_DATE.year)

    base_path = '/tmp/deep_dive/indicator_heatmaps/'
    plot_heatmap_per_indicator(base_path)
