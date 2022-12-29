---
title: Models
---

Here you'll find the models that Post Later uses to manage data.

## Base Models

These are abstract models used as the basis for many of our other model classes.

### `OwnedModel`

::: post_later.models.abstract.OwnedModel
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4
      
### `RemoteUserAuthModel`

::: post_later.models.abstract.RemoteUserAuthModel
    handler: python
    options:
      members:
        - get_avatar_url
        - get_username
        - get_remote_url
        - upload_media
        - send_post
        - username_search
        - is_ready_post
      show_root_toc_entry: false
      heading_level: 4

## Account Models

These are the models that represent each account at the highest level. Any social account auth types
must link to an instance [`Account`](#account), and must be a subclass of [`RemoteUserAuthModel`](#remoteuserauthmodel).

### `Account`

::: post_later.models.social_accounts.Account
    handler: python
    options:
      members:
        - auth_object
        - username
        - avatar_url
        - remote_url
        - refresh_from_db
        - get_absolute_url
      show_root_toc_entry: false
      heading_level: 4
      
### `AccountStats`

::: post_later.models.social_accounts.AccountStats
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4

## Mastodon Models

### `MastodonInstanceClient`

::: post_later.models.mastodon.MastodonInstanceClient
    handler: python
    options:
      members:
        - ready
      show_root_toc_entry: false
      heading_level: 4

### `MastodonUserAuth`

::: post_later.models.mastodon.MastodonUserAuth
    handler: python
    options:
      members:
        - is_ready_post
        - get_avatar_url
        - get_username
        - get_remote_url
      show_root_toc_entry: false
      heading_level: 4

### `MastodonAvatar`

::: post_later.models.mastodon.MastodonAvatar
    handler: python
    options:
      members:
        - get_avatar
        - fetch_avatar
        - img_url
      show_root_toc_entry: false
      heading_level: 4
      
## Twitter Models

To do if Twitter doesn't fall down and explode by the time I get to it.

## Instagram Models

To do if I decide to add support for it. *hisssssss*


## Scheduling Models

These are the models used to scheduling any posts, threads, or media uploads to supported
services.

### `MediaAttachment`

::: post_later.models.statuses.MediaAttachment
    handler: python
    options:
      members:
        - focus
        - is_image
        - is_square_image
        - is_video
        - is_audio
        - generate_thumbnail
        - clean_orphans
        - upload_media
      show_root_toc_entry: false
      heading_level: 4
      
### `ScheduledThread`

::: post_later.models.statuses.ScheduledThread
    handler: python
    options:
      members:
        - num_posts
        - find_jobs
      show_root_toc_entry: false
      heading_level: 4
      show_submodules: true
      
      
### `ScheduledPost`

Note: There may be an arbitrary number of [`MediaAttachment`](#mediaattachment) objects attached to an instance of this.

::: post_later.models.statuses.ScheduledPost
    handler: python
    options:
      members:
        - find_jobs
        - send_post
        - schedule_retry
      show_root_toc_entry: false
      heading_level: 4
      show_submodules: true


