"""
Take in an appeal ID and generate a type "G" FTS report:
Donor
Funding USD
% of Grand Total
Uncommitted pledges USD
"""

import fts_queries
import pandas as pd
import argparse
import sys

parser = argparse.ArgumentParser(description='Produce a FTS type "G" report for a given appeal')
parser.add_argument('appeal_id', type=int)
args = parser.parse_args()
appeal_id = args.appeal_id

funding_by_donor = fts_queries.fetch_funding_json_for_appeal_as_dataframe(appeal_id, grouping='Donor', alias='donor')
pledges_by_donor = fts_queries.fetch_pledges_json_for_appeal_as_dataframe(appeal_id, grouping='Donor', alias='donor')

merged = pd.merge(funding_by_donor, pledges_by_donor, left_index=True, right_index=True, how='inner')
merged['fraction_of_total'] = merged.funding / merged.funding.sum()

merged.to_csv(sys.stdout, index=True, encoding='utf-8')
