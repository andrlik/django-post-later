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
