from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PostLaterConfig(AppConfig):
    """
    Config object for this app.
    """

    name = "post_later"
    verbose_name = _("Post Later")

    def ready(self):
        """
        Initializes receivers at startup.
        """

        try:
            import post_later.receivers  # noqa: F401
        except ImportError:  # pragma: nocover
            pass
