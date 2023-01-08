# Generated by Django 4.1.3 on 2022-12-29 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("post_later", "0016_remove_mediaattachment_video_duration_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduledpost",
            name="queued_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Time this was successfully queued on the remote server.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="scheduledpost",
            name="remote_queue_id",
            field=models.CharField(
                blank=True,
                help_text="Schedule post id if queued on remote server.",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="scheduledthread",
            name="next_retry",
            field=models.DateTimeField(
                blank=True, help_text="If in error, when will we retry next?", null=True
            ),
        ),
        migrations.AddField(
            model_name="scheduledthread",
            name="num_failures",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Number of failures encountered so far sending this thread.",
            ),
        ),
        migrations.AlterField(
            model_name="scheduledpost",
            name="post_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("error", "Error, awaiting retry."),
                    ("failed", "Failed to post after multiple retries. Giving up."),
                    ("queued", "Queued on remote server"),
                    ("complete", "Sucessfully posted."),
                ],
                default="pending",
                help_text="Status of scheduled post.",
                max_length=10,
            ),
        ),
    ]
