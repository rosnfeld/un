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
import os

# TODO extract strings to header section
# TODO should all CSV's have "fts" prefix, e.g. 'fts_sectors.csv', and maybe ISO country code if appropriate?


def write_dataframe_to_csv(dataframe, path):
    print "Writing", path
    # include the index which is an ID for each of the objects serialized by this script
    # use Unicode as many non-ASCII characters
    dataframe.to_csv(path, index=True, encoding='utf-8')


def produce_sectors_csv(output_dir):
    sectors = fts_queries.fetch_sectors_json_as_dataframe()
    write_dataframe_to_csv(sectors, output_dir + 'sectors.csv')


def produce_countries_csv(output_dir):
    countries = fts_queries.fetch_countries_json_as_dataframe()
    write_dataframe_to_csv(countries, output_dir + 'countries.csv')


def produce_organizations_csv(output_dir):
    organizations = fts_queries.fetch_organizations_json_as_dataframe()
    write_dataframe_to_csv(organizations, output_dir + 'organizations.csv')


def produce_global_csvs(base_output_dir):
    # not sure if this directory creation code should be somewhere else..?
    output_dir = base_output_dir + '/fts/global/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    produce_sectors_csv(output_dir)
    produce_countries_csv(output_dir)
    produce_organizations_csv(output_dir)


def produce_emergencies_csv_for_country(output_dir, country):
    emergencies = fts_queries.fetch_emergencies_json_for_country_as_dataframe(country)
    write_dataframe_to_csv(emergencies, output_dir + 'emergencies.csv')


def produce_csvs_for_country(base_output_dir, country):
    output_dir = base_output_dir + '/fts/per_country/' + country + '/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    produce_emergencies_csv_for_country(output_dir, country)

# TODO appeals
# TODO projects
# TODO contributions

if __name__ == "__main__":
    # output all CSVs for a given country to '/tmp/'
    demo_country = 'Chad'
    tmp_output_dir = '/tmp'

    produce_global_csvs(tmp_output_dir)
    produce_csvs_for_country(tmp_output_dir, demo_country)

