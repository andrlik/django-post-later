# Generated by Django 4.1.3 on 2022-12-27 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("post_later", "0011_alter_mastodonuserauth_social_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediaattachment",
            name="remote_id",
            field=models.CharField(
                blank=True,
                help_text="Id for media on remote server if sent.",
                max_length=200,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="scheduledpost",
            name="remote_url",
            field=models.URLField(
                blank=True, help_text="URL to view post on remote server.", null=True
            ),
        ),
    ]
