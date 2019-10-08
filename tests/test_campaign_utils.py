#!/usr/bin/env python3

# Author: Eugene Egbe
# Unit tests for the utility functions in the campaign blueprint

import unittest
import datetime

from isa.campaigns.utils import (get_country_from_code, convert_latin_to_english, compute_campaign_status,
                                 get_all_camapign_stats_data)

from isa.models import Contribution, Campaign


class TestCampaignUtils(unittest.TestCase):
    """Test utility functions in the campaign blueprint."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_country_from_code(self):
        country = get_country_from_code('CM')
        self.assertEqual(country, 'Cameroon')

    def test_convert_latin_to_english(self):
        self.assertEqual(convert_latin_to_english('Třebíč'), 'Trebic')

    def test_compute_campaign_status(self):
        date_time_str = '2018-06-29 08:15'
        end_date = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
        campaign_status = compute_campaign_status(end_date)
        self.assertTrue(campaign_status)

    def test_get_all_camapign_stats_data(self):
        campaign_stats_users = []
        contribution_users = []
        campaign_contributions = Contribution.query.filter_by(campaign_id=1).all()
        all_campaign_stats_data = get_all_camapign_stats_data(1)
        for contribution in campaign_contributions:
            contribution_users.append(contribution.username)
        for stats in all_campaign_stats_data:
            campaign_stats_users.append(stats['username'])
        self.assertEqual(campaign_stats_users, contribution_users)


if __name__ == '__main__':
    unittest.main()
