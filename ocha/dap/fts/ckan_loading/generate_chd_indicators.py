"""
Builds CHD indicators from FTS queries
"""

import fts_queries
import os
import pandas as pd


# note relying on strings is fragile - could break if things get renamed in FTS
# we don't seem to have much in the way of alternatives, other than changing the FTS API
DONOR_ERF = "Emergency Response Fund (OCHA)"
DONOR_CERF = "Central Emergency Response Fund"
DONOR_CHF = "Common Humanitarian Fund"

FUNDING_STATUS_PLEDGE = "Pledge"

ORG_TYPE_NGOS = 'NGOs'
ORG_TYPE_PRIVATE_ORGS = 'Private Orgs. & Foundations'
ORG_TYPE_UN_AGENCIES = 'UN Agencies'


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


def write_values_as_scraperwiki_style_csv(base_dir):
    values = get_values_as_dataframe()
    values['dsID'] = 'fts'
    values['is_number'] = 1
    values['source'] = ''
    values = values.rename(columns={'indicator': 'indID', 'year': 'period'})
    values = values[['dsID', 'region', 'indID', 'period', 'value', 'is_number', 'source']]

    filename = os.path.join(base_dir, 'value.csv')
    values.to_csv(filename, index=False)


def populate_appeals_level_data(country):
    appeals = fts_queries.fetch_appeals_json_for_country_as_dataframe(country)

    # group all appeals by year, columns are now just the numerical ones:
    #  - current_requirements, emergency_id, funding, original_requirements, pledges
    cross_appeals_by_year = appeals.groupby('year').sum().astype(float)

    # iterating by rows is not considered proper form to but it's easier to follow
    for year, row in cross_appeals_by_year.iterrows():
        add_row_to_values('FY010', country, year, row['original_requirements'])
        add_row_to_values('FY020', country, year, row['current_requirements'])
        add_row_to_values('FY040', country, year, row['funding'])

        # note this is a fraction, not a percent, and not clipped to 100%
        add_row_to_values('FY030', country, year, row['funding'] / row['current_requirements'])

    # CAP-only
    cap_appeals = appeals[appeals.type == 'CAP']
    for appeal_id, row in cap_appeals.iterrows():
        add_row_to_values('FA010', country, row['year'], row['current_requirements'])
        add_row_to_values('FA140', country, row['year'], row['funding'])


def get_organizations_indexed_by_name():
    """
    Load organizations from FTS and change index to be name, as sadly that's what is used in
    other API calls, so we need to join on it.
    This is a slow call, so it makes sense to cache it.
    """
    organizations = fts_queries.fetch_organizations_json_as_dataframe()
    return organizations.set_index('name')


def populate_organization_level_data(country, organizations=None):
    if organizations is None:
        organizations = get_organizations_indexed_by_name()

    # load appeals, analyze each one
    appeals = fts_queries.fetch_appeals_json_for_country_as_dataframe(country)

    funding_dataframes_by_appeal = []

    for appeal_id, appeal_row in appeals.iterrows():
        # first check if there is any funding at all (otherwise API calls will get upset)
        if appeal_row['funding'] == 0:
            continue

        # query funding by recipient, including "carry over" from previous years
        funding_by_recipient = fts_queries.fetch_funding_json_for_appeal_as_dataframe(
            appeal_id, grouping='Recipient', alias='organisation')

        funding_by_recipient['year'] = appeal_row['year']

        funding_dataframes_by_appeal.append(funding_by_recipient)

    funding_by_recipient_overall = pd.concat(funding_dataframes_by_appeal)

    # now roll up by organization type
    funding_by_type = funding_by_recipient_overall.join(organizations.type).groupby(['type', 'year']).sum()

    for (org_type, year), row in funding_by_type.iterrows():
        if org_type == ORG_TYPE_NGOS:
            add_row_to_values('FY190', country, year, row['funding'])
        elif org_type == ORG_TYPE_PRIVATE_ORGS:
            add_row_to_values('FY200', country, year, row['funding'])
        elif org_type == ORG_TYPE_UN_AGENCIES:
            add_row_to_values('FY210', country, year, row['funding'])
        else:
            # note that some organizations (e.g. Red Cross/Red Crescent) fall outside the 3 indicator categories
            print 'Ignoring funding for organization type ' + org_type


def populate_pooled_fund_data(country):
    appeals = fts_queries.fetch_appeals_json_for_country_as_dataframe(country)

    contribution_dataframes_by_appeal = []

    for appeal_id, appeal_row in appeals.iterrows():
        contributions = fts_queries.fetch_contributions_json_for_appeal_as_dataframe(appeal_id)

        if contributions.empty:
            continue

        # note that is_allocation field is much cleaner and _almost_ gives the same answer,
        # but found 1 instance of contribution that did not have this set and yet looked like it should
        # TODO look at getting contributions for all appeals up-front and concatenating earlier

        # exclude pledges
        contributions = contributions[contributions.status != FUNDING_STATUS_PLEDGE]

        # exclude non-CERF/ERF/CHF
        donor_filter = lambda x: x in [DONOR_CERF, DONOR_ERF, DONOR_CHF]
        contributions = contributions[contributions.donor.apply(donor_filter)]

        contribution_dataframes_by_appeal.append(contributions)

    contributions_overall = pd.concat(contribution_dataframes_by_appeal)

    # sum amount by donor-year
    amount_by_donor_year = contributions_overall.groupby(['donor', 'year']).amount.sum()

    for (donor, year), amount in amount_by_donor_year.iteritems():
        if donor == DONOR_CERF:
            add_row_to_values('FY240', country, year, amount)
        elif donor == DONOR_ERF:
            add_row_to_values('FY380', country, year, amount)
        elif donor == DONOR_CHF:
            add_row_to_values('FY520', country, year, amount)
        else:
            print 'Ignoring allocated funds for donor:', donor


if __name__ == "__main__":
    regions_of_interest = ['COL', 'KEN', 'YEM']
    # regions_of_interest = ['SSD']  # useful for testing CHF
    organizations = get_organizations_indexed_by_name()

    for region in regions_of_interest:
        populate_appeals_level_data(region)
        populate_organization_level_data(region, organizations)
        populate_pooled_fund_data(region)

    # print get_values_as_dataframe()
    write_values_as_scraperwiki_style_csv('/tmp')
