"""
TN-NT Templates app config
"""

# Django
from django.apps import AppConfig

from . import __version__


class TnntTemplatesConfig(AppConfig):
    """
    Template config
    """

    name = "tnnt_templates"
    label = "tnnt_templates"
    verbose_name = f"Terra Nanotech Alliance Auth Template Overrides v{__version__}"

    def ready(self) -> None:
        """
        App is ready

        :return:
        :rtype:
        """

        # AA Templates: Terra Nanotech
        import tnnt_templates.checks  # noqa: F401 # pylint: disable=unused-import, import-outside-toplevel
