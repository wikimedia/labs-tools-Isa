import sys
from isa import db
from operator import itemgetter
from isa.models import Contribution


def testDbCommitSuccess():
    """
    Test for the success of a database commit operation.

    """
    try:
        db.session.commit()
    except Exception as e:
        print('-------------->>>>>', file=sys.stderr)
        print(str(e), file=sys.stderr)
        db.session.rollback()
        # for resetting non-commited .add()
        db.session.flush()
        return True
    return False


def getCountryRanking(all_contrystats_data, country):
    """
    Get a particular Country's ranking

    Keyword arguments:
    all_contry_stats_data -- sorted list of all country by their contributions
    country -- the country whic's ranking is to be obtained
    """

    index = next((i for i, item in enumerate(all_contrystats_data) if item['country'] == country), -1)
    return index + 1  # we shift from 0


def getCountryContributionImagesImproved(campaign_contributions, country):
    country_improved_files = []
    for contribution in campaign_contributions:
        if contribution.country == country:
            country_improved_files.append(contribution.file)
    return len(country_improved_files)


# TODO: Transfer all these methods to the campaign blueprint
def getCampaignCountryData(campaign_id):
    # Holds contribution countries for campaign with id: campaign_id
    contribution_countries = []

    # Holds all countries and images imaproved per country
    all_country_statistics_data = []

    # We get all the campaign contributions
    campaign_contributions = Contribution.query.filter_by(campaign_id=campaign_id).all()
    # We then iterate to get the countries
    for contribution in campaign_contributions:
        if contribution.country != "":
            contribution_countries.append(contribution.country)
    contribution_countries = set(contribution_countries)

    for country in contribution_countries:
        country_stats_data = {
            'country': country,
            'images_improved': getCountryContributionImagesImproved(campaign_contributions, country)
        }
        all_country_statistics_data.append(country_stats_data)
    all_country_statistics_data = sorted(all_country_statistics_data,
                                         key=itemgetter('images_improved'), reverse=True)

    for country_stats_data in all_country_statistics_data:
        country_stats_data['rank'] = getCountryRanking(all_country_statistics_data, country_stats_data['country'])
    return all_country_statistics_data
