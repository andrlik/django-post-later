# Generated by Django 4.1.3 on 2022-11-10 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("post_later", "0002_mastodonavatar_created_mastodonavatar_modified_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mastodonavatar",
            name="source_url",
            field=models.URLField(
                blank=True, help_text="Original URL from mastodon instance.", null=True
            ),
        ),
    ]
