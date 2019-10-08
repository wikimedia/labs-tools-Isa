#!/usr/bin/env python3

# Author: Eugene Egbe
# Unit tests for the utility functions in the campaign blueprint

import unittest

from isa.campaigns.utils import get_country_from_code, convert_latin_to_english


class TestCampaignUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_country_from_code(self):
        country = get_country_from_code('CM')
        self.assertEqual(country, 'Cameroon')

    def test_convert_latin_to_english(self):
        self.assertEqual(convert_latin_to_english('Třebíč'), 'Trebic')


if __name__ == '__main__':
    unittest.main()
