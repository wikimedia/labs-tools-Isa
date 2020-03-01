#!/usr/bin/env python3

# Author: Eugene Egbe
# Unit tests for the routes in the isa tool

from datetime import datetime
import json
import unittest

from isa import app, db
from isa.models import Campaign


class TestCampaignRoutes(unittest.TestCase):
    test_campaign_id = 0
    # setup and teardown #

    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_TEST_DATABASE_URI']
        self.app = app.test_client()
        db.create_all()

        test_campaign = Campaign(
            campaign_name='Test Campaign',
            categories='[{"name":"Test images","depth":"0"}]',
            campaign_images=100,
            start_date=datetime.strptime('2020-02-01', '%Y-%m-%d'),
            campaign_manager='TestUsername',
            end_date=None,
            status=False,
            short_description='Test campaign for unit test purposes',
            long_description='',
            creation_date=datetime.now().date(),
            depicts_metadata=1,
            campaign_image=None,
            captions_metadata=0,
            campaign_type=0)
        db.session.add(test_campaign)
        db.session.commit()
        self.test_campaign_id = test_campaign.id

    # executed after each test
    def tearDown(self):
        db.session.close()
        db.drop_all()
        pass

    # tests #

    def test_get_campaigns_route(self):
        response = self.app.get('/campaigns', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_get_campaign_by_id(self):
        response = self.app.get('/campaigns/{}'.format(self.test_campaign_id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_get_campaign_categories(self):
        response = self.app.get('/api/get-campaign-categories?campaign={}'.format(self.test_campaign_id), follow_redirects=True)
        data_category = json.loads(response.data.decode('utf-8'))[0]
        campaign = Campaign.query.filter_by(id=self.test_campaign_id).first()
        campaign_category = json.loads(campaign.categories)[0]
        self.assertEqual(data_category['name'], campaign_category['name'])

    def test_contribute_to_campaign(self):
        response = self.app.get('/campaigns/{}/participate'.format(self.test_campaign_id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_get_campaign_stats_by_id(self):
        response = self.app.get('/campaigns/{}/stats'.format(self.test_campaign_id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_update_campaign_images_route(self):
        campaign = Campaign.query.filter_by(id=self.test_campaign_id).first()
        response = self.app.post('/api/update-campaign-images/{}'.format(self.test_campaign_id),
                                 data=json.dumps({'campaign_images': campaign.campaign_images}))
        self.assertEqual(response.data.decode('ascii'), "Success!")

    def test_get_campaign_graph_stats_data(self):
        response = self.app.get('/api/get-campaign-graph-stats-data?campaign={}'.format(self.test_campaign_id), follow_redirects=True)
        # we are only checking if the route part is intact, not the util part
        self.assertEqual(response.status_code, 200)

    def test_search_depicts_no_term(self):
        response = self.app.get('/api/search-depicts/{}'.format(self.test_campaign_id), follow_redirects=True)
        self.assertEqual(json.loads(response.data.decode('utf-8')), {'results': None})

    def test_search_depicts_with_term(self):
        response = self.app.get('/api/search-depicts/{}?q=Wikidata%20Sandbox'.format(self.test_campaign_id), follow_redirects=True)
        self.assertEqual(json.loads(response.data.decode('utf-8'))['results'][0]['id'], 'Q4115189')


if __name__ == '__main__':
    unittest.main()
