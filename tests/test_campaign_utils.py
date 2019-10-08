#!/usr/bin/env python3

# Author: Eugene Egbe
# Unit tests for the utility functions in the campaign blueprint

import unittest

from isa.campaigns.utils import get_country_from_code


class TestCampaignUtils(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_get_country_from_code(self):
        country = get_country_from_code('CM')
        self.assertEqual(country, 'Cameroon')


if __name__ == '__main__':
    unittest.main()
