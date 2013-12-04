"""
Take in an appeal ID and generate a type "D" FTS report:
Cluster
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

parser = argparse.ArgumentParser(description='Produce a FTS type "D" report for a given appeal')
parser.add_argument('appeal_id', type=int)
args = parser.parse_args()
appeal_id = args.appeal_id

cluster_data = fts_queries.fetch_clusters_json_for_appeal_as_dataframe(appeal_id)

# re-arrange columns
cluster_data = pd.DataFrame(cluster_data,
                            columns=['name', 'original_requirement', 'current_requirement', 'funding', 'pledges'])

cluster_data['unmet_requirement'] = cluster_data.current_requirement - cluster_data.funding
# note this is a fraction, not a percent, and not clipped to 100%
cluster_data['fraction_covered'] = cluster_data.funding/cluster_data.current_requirement

#For quick debugging just do: print cluster_data
cluster_data.to_csv(sys.stdout, index=False, encoding='utf-8')
