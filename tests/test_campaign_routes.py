#!/usr/bin/env python3

# Author: Eugene Egbe
# Unit tests for the routes in the isa tool

import json
import unittest

from flask import session

from isa import app
from isa.models import Campaign


class TestCampaignRoutes(unittest.TestCase):
    # setup and teardown #

    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.app = app.test_client()

    # executed after each test
    def tearDown(self):
        pass

    # tests #

    def test_get_campaigns_route(self):
        response = self.app.get('/campaigns', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_get_campaign_by_id(self):
        response = self.app.get('/campaigns/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_get_campaign_categories(self):
        response = self.app.get('/api/get-campaign-categories?campaign=1', follow_redirects=True)
        data_category = json.loads(response.data.decode('utf-8'))[0]
        campaign = Campaign.query.filter_by(id=1).first()
        campaign_category = json.loads(campaign.categories)[0]
        self.assertEqual(data_category['name'], campaign_category['name'])

    def test_contribute_to_campaign(self):
        response = self.app.get('/campaigns/1/participate', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_get_campaign_stats_by_id(self):
        response = self.app.get('/campaigns/1/stats', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_update_campaign_images_route(self):
        campaign = Campaign.query.filter_by(id=1).first()
        response = self.app.post('/api/update-campaign-images/1',
                                 data=json.dumps({'campaign_images': campaign.campaign_images}))
        self.assertEqual(response.data.decode('ascii'), "Success!")


if __name__ == '__main__':
    unittest.main()
