"""
Builds CHD indicators from FTS queries
"""

import fts_queries
import os
import pandas as pd

# holds IndicatorValue objects until we are ready to put them in a dataframe
VALUES = []


class IndicatorValue(object):
    def __init__(self, indicator, region, year, value):
        self.indicator = indicator
        self.region = region
        self.year = year
        self.value = value


def add_row_to_values(indicator, region, year, value):
    VALUES.append(IndicatorValue(indicator, region, year, value))


def get_values_as_dataframe():
    indicators = [ind_value.indicator for ind_value in VALUES]
    regions = [ind_value.region for ind_value in VALUES]
    years = [ind_value.year for ind_value in VALUES]
    values = [ind_value.value for ind_value in VALUES]

    return pd.DataFrame(
        {'indicator': indicators, 'region': regions, 'year': years, 'value': values},
        columns=['indicator', 'region', 'year', 'value']
    )


def populate_appeals_level_data(country):
    appeals = fts_queries.fetch_appeals_json_for_country_as_dataframe(country)

    # group by year, columns are now just the numerical ones:
    #  - current_requirements, emergency_id, funding, original_requirements, pledges
    appeals_by_year = appeals.groupby('year').sum()

    # iterating by rows is not considered proper form to but it's easier to follow
    for year, row in appeals_by_year.iterrows():
        add_row_to_values('FY010', country, year, row['original_requirements'])
        add_row_to_values('FY020', country, year, row['current_requirements'])
        add_row_to_values('FY040', country, year, row['funding'])

        # note this is a fraction, not a percent, and not clipped to 100%
        add_row_to_values('FY030', country, year, row['funding'] / row['current_requirements'])


if __name__ == "__main__":
    populate_appeals_level_data('KEN')
    print get_values_as_dataframe()
