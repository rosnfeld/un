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
            figure = scraperwiki.plot_indicator_timeseries_for_region(dataframe, ind_id, ds_id, region, neighbors)

            if not figure:
                continue

            filename = ind_id.replace('/', '_') + '_' + ds_id + '.png'
            file_path = os.path.join(dir_path, filename)
            print 'Writing', file_path
            figure.savefig(file_path)
            plt.close(figure)
