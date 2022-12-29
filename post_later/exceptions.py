from django.core.exceptions import ImproperlyConfigured


class MediaUploadFailure(Exception):
    """
    Raised when media fails to upload to the remote server.
    """

    pass


class PostSendFailure(Exception):
    """
    Raised when a post is sent to a remote server and fails.
    """

    pass


class ThreadSendFailure(Exception):
    """
    Raised when a thread attempts to send to a remote server and fails.
    """

    pass


class MissingSettingsError(ImproperlyConfigured):
    """
    Raised when essential settings are missing from the Django project.
    """

    pass
