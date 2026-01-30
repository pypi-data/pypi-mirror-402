"""
Test the AppSettings class
"""

# Standard Library
from unittest.mock import patch

# Django
from django.conf import settings

# AA Templates: Terra Nanotech
from tnnt_templates.app_settings import AppSettings, _clean_setting
from tnnt_templates.tests import BaseTestCase


class TestHelperCleanSetting(BaseTestCase):
    """
    Tests for the _clean_setting helper function
    """

    def test_returns_default_value_when_setting_is_absent(self):
        """
        Test returns default value when setting is absent

        :return:
        :rtype:
        """

        if hasattr(settings, "TEST_SETTING"):
            delattr(settings, "TEST_SETTING")

        result = _clean_setting("TEST_SETTING", default_value=123, required_type=int)

        self.assertEqual(result, 123)

    def test_returns_setting_value_when_valid_and_defined(self):
        """
        Test returns setting value when valid and defined

        :return:
        :rtype:
        """

        with self.settings(TEST_SETTING=456):
            result = _clean_setting(
                "TEST_SETTING", default_value=123, required_type=int
            )

            self.assertEqual(result, 456)

    def test_raises_value_error_when_default_is_below_minimum(self):
        """
        Test raises ValueError when default is below minimum

        :return:
        :rtype:
        """

        with self.assertRaises(ValueError):
            _clean_setting(
                "TEST_SETTING", default_value=5, min_value=10, required_type=int
            )

    def test_raises_value_error_when_default_exceeds_maximum(self):
        """
        Test raises ValueError when default exceeds maximum

        :return:
        :rtype:
        """

        with self.assertRaises(ValueError):
            _clean_setting(
                "TEST_SETTING", default_value=15, max_value=10, required_type=int
            )

    def test_uses_minimum_value_when_setting_is_below_minimum(self):
        """
        Test uses minimum value when setting is below minimum

        :return:
        :rtype:
        """

        with self.settings(TEST_SETTING=5):
            result = _clean_setting(
                "TEST_SETTING", default_value=123, min_value=10, required_type=int
            )

            self.assertEqual(result, 10)

    def test_uses_maximum_value_when_setting_exceeds_maximum(self):
        """
        Test uses maximum value when setting exceeds maximum

        :return:
        :rtype:
        """

        with self.settings(TEST_SETTING=15):
            result = _clean_setting(
                "TEST_SETTING", default_value=3, max_value=10, required_type=int
            )

            self.assertEqual(result, 10)

    def test_raises_type_error_when_required_type_is_invalid(self):
        """
        Test raises TypeError when required_type is invalid

        :return:
        :rtype:
        """

        with self.assertRaises(TypeError):
            _clean_setting(
                "TEST_SETTING", default_value=123, required_type="not_a_type"
            )

    def test_raises_value_error_when_required_type_is_missing_for_none_default(self):
        """
        Test raises ValueError when required_type is missing for None default

        :return:
        :rtype:
        """

        with self.assertRaises(ValueError):
            _clean_setting("TEST_SETTING", default_value=None)

    def test_uses_default_value_when_setting_is_not_in_choices(self):
        """
        Test uses default value when setting is not in choices

        :return:
        :rtype:
        """

        with self.settings(TEST_SETTING=999):
            result = _clean_setting(
                "TEST_SETTING", default_value=123, required_type=int, choices=[1, 2, 3]
            )

            self.assertEqual(result, 123)

    def test_uses_setting_value_when_in_choices(self):
        """
        Test uses setting value when in choices

        :return:
        :rtype:
        """

        with self.settings(TEST_SETTING=2):
            result = _clean_setting(
                "TEST_SETTING", default_value=123, required_type=int, choices=[1, 2, 3]
            )

            self.assertEqual(result, 2)

    def test_uses_type_of_default_value_when_required_type_is_not_provided(self):
        """
        Test uses type of default value when required_type is not provided

        :return:
        :rtype:
        """

        result = _clean_setting("TEST_SETTING", default_value=123)

        self.assertEqual(result, 123)

    def test_raises_type_error_when_default_value_is_none_and_required_type_is_not_provided(
        self,
    ):
        """
        Test raises TypeError when default_value is None and required_type is not provided

        :return:
        :rtype:
        """

        with self.assertRaises(ValueError):
            _clean_setting("TEST_SETTING", default_value=None)

    def test_does_not_raise_error_when_required_type_is_subclass_of_int(self):
        """
        Test does not raise error when required_type is subclass of int

        :return:
        :rtype:
        """

        result = _clean_setting("TEST_SETTING", default_value=123, required_type=int)

        self.assertEqual(result, 123)

    def test_skips_check_when_default_value_is_none_and_required_type_is_subclass_of_int(
        self,
    ):
        """
        Test skips check when default_value is None and required_type is subclass of int

        :return:
        :rtype:
        """

        result = _clean_setting("TEST_SETTING", default_value=None, required_type=int)

        self.assertIsNone(result)


class TestAppSettings(BaseTestCase):
    """
    Test the AppSettings class
    """

    @patch("django.apps.apps.is_installed", return_value=True)
    def test_aagdpr_installed_returns_true(self, mock_is_installed):
        """
        Test the aagdpr_installed method when aagdpr is installed

        :param mock_is_installed:
        :type mock_is_installed:
        :return:
        :rtype:
        """

        self.assertTrue(AppSettings.aagdpr_installed())

    @patch("django.apps.apps.is_installed", return_value=False)
    def test_aagdpr_installed_returns_false(self, mock_is_installed):
        """
        Test the aagdpr_installed method when aagdpr is not installed

        :param mock_is_installed:
        :type mock_is_installed:
        :return:
        :rtype:
        """

        self.assertFalse(AppSettings.aagdpr_installed())
