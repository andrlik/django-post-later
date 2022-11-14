Views for Post Later are documented below.

## Mastodon Account Management

The flow for linking a new Mastodon account is as follows.

1. The user navigates to [`MastodonAccountAddView`](#mastodonaccountaddview) and is prompted to enter the URL for their Mastodon instance.
2. Post Later either retrieves an existing client for that instance, or creates a new one, and then redirects to that instances OAuth Authorization page.
3. The Mastodon instance then redirects the user to [`HandleMastodonAuthView`](#handlemastodonauthview) which saves the OAuth token and redirects to [`MastodonLoginView`](#mastodonloginview).
4. [`MastodonLoginView`](#mastodonloginview) sends a request for an auth token from the Mastodon instance and saves it. At this point, the account is fully authorized, and it submits a request for screenname and avatar information to save accordingly. This should also trigger the async fetch of the cached avatar file, but this is **not implemented yet**.
5. The user is then redirected to [`MastodonAccountDetailView`](#mastodonaccountdetailview).

### `MastodonAccountAddView`

::: post_later.views.mastodon.MastodonAccountAddView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4


### `HandleMastodonAuthView`

::: post_later.views.mastodon.HandleMastodonAuthView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4


### `MastodonLoginView`

::: post_later.views.mastodon.MastodonLoginView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4

### `MastodonAccountDetailView`

::: post_later.views.mastodon.MastodonAccountDetailView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4


### `MastodonAccountListView`

::: post_later.views.mastodon.MastodonAccountListView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4

### `MastodonAccountDeleteView`

::: post_later.views.mastodon.MastodonAccountDeleteView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4
