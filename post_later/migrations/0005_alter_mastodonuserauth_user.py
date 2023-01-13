# Generated by Django 4.1.3 on 2022-11-21 15:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("post_later", "0004_alter_mastodoninstanceclient_client_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mastodonuserauth",
            name="user",
            field=models.ForeignKey(
                help_text="The user object that owns this instance.",
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]