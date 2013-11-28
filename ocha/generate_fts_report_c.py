"""
Take in an appeal ID and generate a type "C" FTS report:
Appealing Org
Original Requirements USD
Revised Requirements USD
Carry Over USD - this is currently not broken out, though could be
Funding USD - this is the funding (contributions + commitments) separate from carry over, also not currently broken out
Total Resources Available USD
Unmet Requirements USD
% Covered
Uncommitted pledges USD
"""

import fts_queries
import pandas as pd
import argparse
import sys

parser = argparse.ArgumentParser(description='Produce a FTS type "C" report for a given appeal')
parser.add_argument('appeal_id', type=int)
args = parser.parse_args()
appeal_id = args.appeal_id

# load the projects dataset, and then group projects by organization
projects = fts_queries.fetch_projects_json_for_appeal_as_dataframe(appeal_id)
projects_by_org = projects.groupby(['organisation', 'organisation_abbreviation'])

# extract out the columns we're interested in
requirements = projects_by_org['original_requirements', 'current_requirements'].sum()

# make organisation_abbreviation a column and no longer part of the index
requirements = requirements.reset_index(level=1)

# query funding, which includes "carry over" from previous years
funding_by_recipient =\
    fts_queries.fetch_funding_json_for_appeal_as_dataframe(appeal_id, grouping='Recipient', alias='organisation')

# join the requirements with the funding
merged = pd.merge(requirements, funding_by_recipient, left_index=True, right_index=True, how='left')

# do the same thing with pledges
pledges_by_recipient =\
    fts_queries.fetch_pledges_json_for_appeal_as_dataframe(appeal_id, grouping='Recipient', alias='organisation')

merged = pd.merge(merged, pledges_by_recipient, left_index=True, right_index=True, how='left')

# fill in any entries where we didn't get pledges or funding data as zero
merged = merged.fillna(0)

merged['unmet_requirements'] = merged.current_requirements - merged.funding
# note this is a fraction, not a percent, and not clipped to 100%
merged['fraction_covered'] = merged.funding/merged.current_requirements

#For quick debugging just do: print merged.head()
merged.to_csv(sys.stdout, index=False, encoding='utf-8')
