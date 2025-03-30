import unittest
from unittest.mock import patch

from isa.utils.context_processors import rtl_context_processor


class TestContextProcessors(unittest.TestCase):
    """Test context processors."""

    def test_rtl_context_processor_en(self):
        with patch('isa.utils.context_processors.session') as mock_session:
            mock_session.get.return_value = 'en'
            context = rtl_context_processor()
            self.assertEqual(context, {'is_rtl': False})

    def test_rtl_context_processor_ar(self):
        with patch('isa.utils.context_processors.session') as mock_session:
            mock_session.get.return_value = 'ar'
            context = rtl_context_processor()
            self.assertEqual(context, {'is_rtl': True})

    def test_rtl_context_processor_default(self):
        with patch('isa.utils.context_processors.session') as mock_session:
            mock_session.get.return_value = None  # Simulate no language in session, defaults to 'en'
            context = rtl_context_processor()
            self.assertEqual(context, {'is_rtl': False})


if __name__ == '__main__':
    unittest.main()
