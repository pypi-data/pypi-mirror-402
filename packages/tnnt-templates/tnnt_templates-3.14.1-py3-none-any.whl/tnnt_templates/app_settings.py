"""
App settings
"""

# Standard Library
from typing import Any

# Django
from django.apps import apps
from django.conf import settings

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Templates: Terra Nanotech
from tnnt_templates import __title__
from tnnt_templates.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(name=__name__), prefix=__title__)


def _clean_setting(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    name: str,
    default_value: Any,
    min_value: int | None = None,
    max_value: int | None = None,
    required_type: type | None = None,
    choices: list | None = None,
) -> Any:
    """
    Clean a setting from Django settings.

    Will use default_value if setting is not defined.
    Will use minimum or maximum value if respective boundary is exceeded.

    :param name:
    :type name:
    :param default_value:
    :type default_value:
    :param min_value:
    :type min_value:
    :param max_value:
    :type max_value:
    :param required_type:
    :type required_type:
    :param choices:
    :type choices:
    :return:
    :rtype:
    """

    if default_value is None and not required_type:
        raise ValueError("You must specify a required_type for None defaults")

    required_type_2 = type(default_value) if required_type is None else required_type

    if not isinstance(required_type_2, type):
        raise TypeError("required_type must be a type when defined")

    if min_value is None and issubclass(required_type_2, int):
        min_value = 0

    if issubclass(required_type_2, int) and default_value is not None:
        if min_value is not None and default_value < min_value:
            raise ValueError("default_value can not be below min_value")

        if max_value is not None and default_value > max_value:
            raise ValueError("default_value can not be above max_value")

    if not hasattr(settings, name):
        cleaned_value = default_value
    else:
        dirty_value = getattr(settings, name)

        if dirty_value is None or (
            isinstance(dirty_value, required_type_2)
            and all(
                (
                    min_value is None or dirty_value >= min_value,
                    max_value is None or dirty_value <= max_value,
                    choices is None or dirty_value in choices,
                )
            )
        ):
            cleaned_value = dirty_value
        elif (
            isinstance(dirty_value, required_type_2)
            and min_value is not None
            and dirty_value < min_value
        ):
            logger.warning(
                "You setting for %s it not valid. Please correct it. "
                "Using minimum value for now: %s",
                name,
                min_value,
            )
            cleaned_value = min_value
        elif (
            isinstance(dirty_value, required_type_2)
            and max_value is not None
            and dirty_value > max_value
        ):
            logger.warning(
                "You setting for %s it not valid. Please correct it. "
                "Using maximum value for now: %s",
                name,
                max_value,
            )
            cleaned_value = max_value
        else:
            logger.warning(
                "You setting for %s it not valid. Please correct it. "
                "Using default for now: %s",
                name,
                default_value,
            )
            cleaned_value = default_value

    return cleaned_value


class AppSettings:  # pylint: disable=too-few-public-methods
    """
    App settings from local.py
    """

    TNNT_TEMPLATE_ENTITY_TYPE = _clean_setting(
        name="TNNT_TEMPLATE_ENTITY_TYPE", default_value="alliance", required_type=str
    )

    TNNT_TEMPLATE_ENTITY_ID = _clean_setting(
        name="TNNT_TEMPLATE_ENTITY_ID", default_value=1, required_type=int
    )

    TNNT_TEMPLATE_ENTITY_NAME = _clean_setting(
        name="TNNT_TEMPLATE_ENTITY_NAME", default_value="", required_type=str
    )

    @staticmethod
    def aagdpr_installed() -> bool:
        """
        Check if aagdpr is installed
        """

        return apps.is_installed("aagdpr")
