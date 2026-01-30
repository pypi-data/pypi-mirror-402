"""
Unit tests for TN-NT Template tags

This module contains unit tests for custom template tags used in the TN-NT Auth Theme.
The tests ensure that the template tags behave as expected under various conditions.
"""

# Django
from django.template import Context, Template
from django.test import modify_settings

# AA Templates: Terra Nanotech
from tnnt_templates import __version__
from tnnt_templates.templatetags.tnnt_templates import startswith
from tnnt_templates.tests import BaseTestCase


class TestFilterStartsWith(BaseTestCase):
    """
    Unit test class for the `startswith` template filter.
    """

    def test_returns_true_when_haystack_starts_with_needle(self):
        """
        Tests that the `startswith` filter returns True when the haystack starts with the needle.

        :return:
        :rtype:
        """

        self.assertTrue(startswith("hello world", "hello"))

    def test_returns_false_when_haystack_does_not_start_with_needle(self):
        """
        Tests that the `startswith` filter returns False when the haystack does not start with the needle.

        :return:
        :rtype:
        """

        self.assertFalse(startswith("hello world", "world"))

    def test_returns_true_when_needle_is_empty(self):
        """
        Tests that the `startswith` filter returns True when the needle is an empty string.

        :return:
        :rtype:
        """

        self.assertTrue(startswith("haystack", ""))

    def test_returns_true_when_both_haystack_and_needle_are_empty(self):
        """
        Tests that the `startswith` filter returns True when both haystack and needle are empty strings.

        :return:
        :rtype:
        """

        self.assertTrue(startswith("", ""))

    def test_is_case_sensitive(self):
        """
        Tests that the `startswith` filter is case-sensitive.

        :return:
        :rtype:
        """

        self.assertFalse(startswith("Hello World", "hello"))

    def test_raises_type_error_when_needle_is_none(self):
        """
        Tests that the `startswith` filter raises a TypeError when the needle is None.

        :return:
        :rtype:
        """

        with self.assertRaises(TypeError):
            startswith("haystack", None)

    def test_raises_attribute_error_when_haystack_is_none(self):
        """
        Tests that the `startswith` filter raises an AttributeError when the haystack is None.

        :return:
        :rtype:
        """

        with self.assertRaises(AttributeError):
            startswith(None, "needle")

    def test_raises_attribute_error_for_non_string_haystack(self):
        """
        Tests that the `startswith` filter raises an AttributeError when the haystack is not a string.

        :return:
        :rtype:
        """

        with self.assertRaises(AttributeError):
            startswith(12345, "12")


class TestTagIsAppInstalled(BaseTestCase):
    """
    Unit test class for the `is_app_installed` template tag.
    """

    @modify_settings(INSTALLED_APPS={"append": "aagdpr"})
    def test_should_return_true_when_app_is_installed(self):
        """
        Tests that the template renders 'True' when the specified app is installed.

        This test verifies the behavior of the custom `is_app_installed` template tag
        by appending the app "aagdpr" to the `INSTALLED_APPS` setting. It ensures
        that the template correctly identifies the app as installed and renders 'True'.

        :return: None
        """

        template_to_render = Template(
            "{% load tnnt_templates %}"
            '{% is_app_installed "aagdpr" as is_myapp_installed %}'
            "{% if is_myapp_installed %}True{% else %}False{% endif %}"
        )
        rendered_template = template_to_render.render(Context({"version": __version__}))

        self.assertEqual(rendered_template, "True")

    @modify_settings(INSTALLED_APPS={"remove": "aagdpr"})
    def test_should_return_false_when_app_is_not_installed(self):
        """
        Tests that the template renders 'False' when the specified app is not installed.

        This test verifies the behavior of the custom `is_app_installed` template tag
        by removing the app "aagdpr" from the `INSTALLED_APPS` setting. It ensures
        that the template correctly identifies the app as not installed and renders 'False'.

        :return: None
        """

        template_to_render = Template(
            "{% load tnnt_templates %}"
            '{% is_app_installed "aagdpr" as is_myapp_installed %}'
            "{% if is_myapp_installed %}True{% else %}False{% endif %}"
        )
        rendered_template = template_to_render.render(Context({"version": __version__}))

        self.assertEqual(rendered_template, "False")
