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


class ThreadAlreadyComplete(Exception):
    """
    Raised when trying to ask a thread to send posts when it is already in a Failed or
    Complete state.
    """

    pass


class EmptyThreadException(Exception):
    """
    Raised when trying to query the next post for a thread, but it doesn't exist in the database.
    """

    pass


class BoostSendFailure(Exception):
    """
    Raised when a boost fails to send.
    """

    pass


class MissingSettingsError(ImproperlyConfigured):
    """
    Raised when essential settings are missing from the Django project.
    """

    pass
