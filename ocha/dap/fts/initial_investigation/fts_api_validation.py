import fts_queries


def confirm_country_for_every_appeal():
    """
    Confirm that every appeal has a country entry (this would have failed on legit countries up until recently)
    """
    countries = fts_queries.fetch_countries_json_as_dataframe()
    appeals_2013 = fts_queries.fetch_appeals_json_for_year_as_dataframe(2013)
    for appeal_id, appeal_row in appeals_2013.iterrows():
        appeal_country = appeal_row['country']
        matching_countries_boolean_series = (countries.name == appeal_country)
        if matching_countries_boolean_series.sum() != 1:
            print "No country entry found for appeal", appeal_id, "which has country", appeal_country
            #print appeal_row


def confirm_country_for_every_emergency():
    """
    Confirm that every emergency has a country entry
    """
    countries = fts_queries.fetch_countries_json_as_dataframe()
    emergencies_2013 = fts_queries.fetch_emergencies_json_for_year_as_dataframe(2013)
    for emergency_id, emergency_row in emergencies_2013.iterrows():
        emergency_country = emergency_row['country']
        matching_countries_boolean_series = (countries.name == emergency_country)
        if matching_countries_boolean_series.sum() != 1:
            print "No country entry found for emergency", emergency_id, "which has country", emergency_country
            #print emergency_row


if __name__ == "__main__":
    confirm_country_for_every_appeal()
    confirm_country_for_every_emergency()
