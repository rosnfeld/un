"""
Take in an appeal ID and generate a report on CERF and ERF funding by cluster:
Cluster
CERF Funding USD - contributions + commitments
ERF Funding USD - contributions + commitments
"""

import fts_queries
import pandas as pd
import argparse
import sys

parser = argparse.ArgumentParser(description='Produce a report on CERF and ERF funding by cluster for a given appeal')
parser.add_argument('appeal_id', type=int)
args = parser.parse_args()
appeal_id = args.appeal_id

# note relying on strings is fragile - could break if things get renamed in FTS
# we don't seem to have much in the way of alternatives, other than changing the FTS API
CERF_NAME = "Central Emergency Response Fund"
ERF_NAME = "Emergency Response Fund (OCHA)"
PLEDGE_NAME = "Pledge"

contributions = fts_queries.fetch_contributions_json_for_appeal_as_dataframe(appeal_id)
projects = fts_queries.fetch_projects_json_for_appeal_as_dataframe(appeal_id)

# join contributions with the associated project data
merged = pd.merge(contributions, projects, left_on='project_code', right_on='code', how='inner')

# exclude pledges
merged = merged[merged.status != PLEDGE_NAME]

# pivot, summing amount by cluster and donor
pivot = merged.pivot_table(values='amount', aggfunc='sum', rows=['cluster'], cols=['donor'])

# only keep CERF/ERF
pivot_slice = pivot[[CERF_NAME, ERF_NAME]]

# TODO could left join with sectors and fillna(0) to make sure all sectors are present in report, even if not funded

pivot_slice.to_csv(sys.stdout, index=True, encoding='utf-8')
