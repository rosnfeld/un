"""
Can be used to produce the following CSV files for upload into CKAN:
  - sectors.csv
  - countries.csv
  - organizations.csv
  - emergencies.csv (for a given country)
  - appeals.csv (for a given country)
  - projects.csv (for a given country, based on appeals)
  - contributions.csv (for given country, based on emergencies, which should capture all appeals, also)
"""

import fts_queries


# TODO progress logging would be nice, e.g. "Writing foo.csv"
# TODO extract strings to header section
# TODO should all CSV's have "fts" prefix, e.g. 'fts_sectors.csv'?
# TODO should we build subdirs for staging
#  - maybe try this structure: <output_dir>/fts/global/..., <output_dir>/fts/per_country/<country>/...
#  - I think that maybe makes more sense than namespacing in filename... or could do both?


def produce_sectors_csv(output_dir):
    sectors = fts_queries.fetch_sectors_json_as_dataframe()
    sectors.to_csv(output_dir + '/sectors.csv', index=True, encoding='utf-8')


def produce_countries_csv(output_dir):
    countries = fts_queries.fetch_countries_json_as_dataframe()
    countries.to_csv(output_dir + '/countries.csv', index=True, encoding='utf-8')


def produce_organizations_csv(output_dir):
    organizations = fts_queries.fetch_organizations_json_as_dataframe()
    organizations.to_csv(output_dir + '/organizations.csv', index=True, encoding='utf-8')


def produce_global_csvs(output_dir):
    produce_sectors_csv(output_dir)
    produce_countries_csv(output_dir)
    produce_organizations_csv(output_dir)


# def produce_emergencies_csv_for_country(output_dir, country):
#     emergencies = fts_queries.fetch_emergencies_json_for_country_as_dataframe(country)
#     emergencies.to_csv(output_dir + '/emergencies.csv', index=True, encoding='utf-8')
#
# def produce_csvs_for_country(output_dir, country):
#     # TODO modify output_dir here?
#     produce_emergencies_csv_for_country(output_dir, country)


if __name__ == "__main__":
    # output all CSVs for a given country to '/tmp/'
    country = 'Chad'
    output_dir = '/tmp/'

    produce_global_csvs(output_dir)

