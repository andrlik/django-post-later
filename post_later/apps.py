from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .exceptions import MissingSettingsError


class PostLaterConfig(AppConfig):
    """
    Config object for this app.
    """

    name = "post_later"
    verbose_name = _("Post Later")

    def ready(self):
        """
        Checks configs and Initializes receivers at startup.
        """
        required_settings = [
            "CLIENT_NAME",
            "ENABLED_ACCOUNT_TYPES",
            "MAX_POST_FAILURES",
            "POST_FAILURE_RETRY_RATE",
        ]
        for setting in required_settings:
            if not hasattr(settings, setting):
                raise MissingSettingsError(
                    f"Post Later Impropery Configured: You must specify {setting} in your settings file."
                )
        # if "TWITTER" in settings.ENABLED_ACCOUNT_TYPES:
        #     for setting in [
        #         "TWITTER_CONSUMER_KEY",
        #         "TWITTER_CONSUMER_SECRET",
        #         "TWITTER_CALLBACK_URL",
        #     ]:
        #         if (
        #             not hasattr(settings, setting)
        #             or getattr(settings, setting) is None
        #             or getattr(settings, setting) == ""
        #         ):
        #             raise MissingSettingsError(
        #                 f"Post Later Improperly Configured: Account type 'TWITTER' is enabled, but {setting} is missing from settings file."  # noqa: E501
        #             )
        try:
            import post_later.receivers  # noqa: F401
        except ImportError:  # pragma: nocover
            pass
