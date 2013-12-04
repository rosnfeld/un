"""
Take in an emergency ID and generate a report on ERF donations (should cover CHD FY380):
Donor
ERF Commitment USD
ERF Paid contribution
ERF Pledge USD
ERF All USD
"""

import fts_queries
import argparse
import sys

parser = argparse.ArgumentParser(description='Produce a report on ERF donations for a given emergency')
parser.add_argument('emergency_id', type=int)
args = parser.parse_args()
emergency_id = args.emergency_id

# note relying on strings is fragile - could break if things get renamed in FTS
# we don't seem to have much in the way of alternatives, other than changing the FTS API
ERF_NAME = "Emergency Response Fund (OCHA)"

contributions = fts_queries.fetch_contributions_json_for_emergency_as_dataframe(emergency_id)

# filter to just ERF contributions
# note that this contains a "Balancing entry pf ERF allocations" that backs out the amount allocated, as a commitment
erf_contributions = contributions[contributions.recipient == ERF_NAME]

# pivot amount by donor and status
pivot = erf_contributions.pivot_table(values='amount', aggfunc='sum', rows=['donor'], cols=['status'], margins=True)

pivot.to_csv(sys.stdout, index=True, encoding='utf-8')
