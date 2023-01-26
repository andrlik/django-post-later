import os
import sys

from pydantic import AnyUrl, BaseSettings, Field, validator


class ImplicitHostName(AnyUrl):
    host_required = False


POSTLATER_ENV_FILE = os.environ.get(
    "POSTLATER_ENV_FILE", "test.env" if "pytest" in sys.modules else ".env"
)


class PLSettings(BaseSettings):
    """
    Settings via Pydantic
    """

    #: The default client name.
    CLIENT_NAME: str = "Post Later"

    #: Default max image size for an attachment.
    MAX_POST_IMAGE_SIZE: int = 8

    #: Default max video size for an attachment.
    MAX_POST_VIDEO_SIZE: int = 40

    #: Account types enabled, e.g. ["MASTODON", "INSTAGRAM", "TWITTER"]
    ENABLED_ACCOUNT_TYPES: list[str] = Field(default_factory=list)

    #: Default number of failures to accept before giving up.
    MAX_POST_FAILURES: int = 20

    #: Default time in seconds to wait before trying to resend a failed post.
    POST_FAILURE_RETRY_WAIT: int = 4800

    #: Default time to allow a job to be locked.

    DEFAULT_JOB_LOCK_SECONDS: int = 4800

    TWITTER_CONSUMER_KEY: str | None = None
    TWITTER_CONSUMER_SECRET: str | None = None
    TWITTER_CALLBACK_URL: AnyUrl | None = "http://127.0.0.1:8000/twitterauth/callback/"

    @validator("ENABLED_ACCOUNT_TYPES", always=True)
    def validate_account_types(cls, ENABLED_ACCOUNT_TYPES):
        """
        Verifies that the configured account types have at least one value and all the
        types set are among those supported.
        """
        assert len(ENABLED_ACCOUNT_TYPES) > 0, "must include at least one account type"
        for at in ENABLED_ACCOUNT_TYPES:
            assert at in [
                "MASTODON",
                "TWITTER",
                "INSTAGRAM",
            ], 'must be one of "MASTODON", "TWITTER", or "INSTAGRAM"'
        return ENABLED_ACCOUNT_TYPES

    @validator("TWITTER_CONSUMER_KEY", always=True, allow_reuse=True)
    @validator("TWITTER_CONSUMER_SECRET", always=True, allow_reuse=True)
    @validator("TWITTER_CALLBACK_URL", always=True, allow_reuse=True)
    def twitter_settings_provided(cls, v, values):
        """
        Verifies that if TWITTER support is enabled that the proper
        twitter configuration is set.
        """
        if "TWITTER" in values.get("ENABLED_ACCOUNT_TYPES"):
            assert (
                v is not None and v != ""
            ), "must be provided if twitter connections are enabled"
        return v

    class Config:
        env_prefix = "POSTLATER_"
        env_file = str(POSTLATER_ENV_FILE)
        env_file_encoding = "utf-8"
