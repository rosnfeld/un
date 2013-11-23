"""
Take in an appeal ID and generate a report on funding by appealing agency type (roughly CHD items FY180 through FY210)
Appealing Org Type
Funding USD - contributions + commitments, including carry-over from previous year
"""

import fts_queries
import argparse
import sys

parser = argparse.ArgumentParser(description='Produce a report on funding by agency type for a given appeal')
parser.add_argument('appeal_id', type=int)
args = parser.parse_args()
appeal_id = args.appeal_id

# load organizations dataset
organizations = fts_queries.fetch_organizations_json_as_dataframe()
# we'll be joining on name (sadly) so make that the index
organizations = organizations.set_index('name')
# extract out the types Series
organizations_type = organizations.type

# query funding, which includes "carry over" from previous years
funding_by_recipient = fts_queries.fetch_funding_json_for_appeal_as_dataframe(appeal_id, grouping='Recipient')
# set up the index for the join on organisation name
funding_by_recipient = funding_by_recipient.rename(columns={'type': 'organisation', 'amount': 'funding_amount'})
funding_by_recipient = funding_by_recipient.set_index('organisation')

# join the funding with the organization type
joined = funding_by_recipient.join(organizations_type)

# now roll up by organization type
aggregated = joined.groupby('type').sum()

aggregated.to_csv(sys.stdout, index=True, encoding='utf-8')
