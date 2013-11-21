"""
Take in an appeal ID and generate a type "C" FTS report:
Appealing Org
Original Requirements USD
Revised Requirements USD
Carry Over USD
Funding USD
Total Resources Available USD
Unmet Requirements USD
% Covered
Uncommitted pledges USD
"""

import fts_queries
import pandas as pd

# TODO take a command line argument
appeal_id = 989

# load the projects dataset, and then group projects by organization
projects = fts_queries.fetch_projects_json_for_appeal_as_dataframe(appeal_id)
projects_by_org = projects.groupby(['organisation', 'organisation_abbreviation'])

# extract out the columns we're interested in
requirements = projects_by_org['original_requirements', 'current_requirements'].sum()

# make organisation_abbreviation a column and no longer part of the index
requirements = requirements.reset_index(level=1)

# query funding, which interestingly seems to include "carry over" from previous years
# TODO figure out how to break out "carry over" - may actually need to look at contributions
# however, note that the CHD does not require carry over
funding_by_recipient = fts_queries.fetch_funding_json_for_appeal_as_dataframe(appeal_id, grouping='Recipient')
# set up the index for the join
funding_by_recipient = funding_by_recipient.rename(columns={'type': 'organisation', 'amount': 'funding_amount'})
funding_by_recipient = funding_by_recipient.set_index('organisation')

# join the requirements with the funding
merged = pd.merge(requirements, funding_by_recipient, left_index=True, right_index=True, how='left')

# do the same thing with pledges
pledges_by_recipient = fts_queries.fetch_pledges_json_for_appeal_as_dataframe(appeal_id, grouping='Recipient')
pledges_by_recipient = pledges_by_recipient.rename(columns={'type': 'organisation', 'amount': 'pledged_amount'})
pledges_by_recipient = pledges_by_recipient.set_index('organisation')

merged = pd.merge(merged, pledges_by_recipient, left_index=True, right_index=True, how='left')

# fill in any entries where we didn't get pledges or funding data as zero
merged = merged.fillna(0)

merged['unmet_requirements'] = merged.current_requirements - merged.funding_amount
merged['fraction_covered'] = merged.funding_amount/merged.current_requirements

#TODO output CSV

print merged.head()
