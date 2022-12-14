# Generated by Django 4.1.3 on 2022-11-09 19:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import post_later.models.mastodon


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MastodonInstanceClient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "api_base_url",
                    models.URLField(
                        help_text="Unique url for instance, e.g. https://mastodon.social",
                        unique=True,
                    ),
                ),
                (
                    "client_id",
                    models.CharField(
                        help_text="Unique client id for instance.",
                        max_length=100,
                        verbose_name="Client Id",
                    ),
                ),
                (
                    "client_secret",
                    models.CharField(
                        help_text="Client secret token for instance.",
                        max_length=100,
                        verbose_name="Client Secret",
                    ),
                ),
                (
                    "vapid_key",
                    models.CharField(
                        blank=True,
                        help_text="Optional. Vapid key for use in receiving push notifications is server supports it.",
                        max_length=250,
                        null=True,
                        verbose_name="Vapid Key",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MastodonUserAuth",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "account_username",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "user_oauth_key",
                    models.CharField(
                        blank=True,
                        help_text="Users OAuth code.",
                        max_length=250,
                        null=True,
                    ),
                ),
                (
                    "user_auth_token",
                    models.CharField(
                        blank=True,
                        help_text="Current auth token for user session.",
                        max_length=250,
                        null=True,
                    ),
                ),
                (
                    "instance_client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="post_later.mastodoninstanceclient",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MastodonAvatar",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "source_url",
                    models.URLField(help_text="Original URL from mastodon instance."),
                ),
                (
                    "cached_avatar",
                    models.ImageField(
                        blank=True,
                        help_text="Locally cached version of avatar.",
                        null=True,
                        upload_to=post_later.models.mastodon.mastodon_account_directory_path,
                    ),
                ),
                (
                    "cache_stale",
                    models.BooleanField(
                        default=True,
                        help_text="Should we refresh the cached image at next opportunity?",
                    ),
                ),
                (
                    "user_account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="post_later.mastodonuserauth",
                    ),
                ),
            ],
        ),
    ]
