Views for Post Later are documented below.

## Account Management Views

The flow for the account management views is as follows.

1. The user navigates to [`AccountCreateView`](#accountcreateview) is is prompted to choose the type of social account they want to link.
2. The view then redirects the user to the associated account creation view for the given service, e.g. [`MastodonAccountAddView`], and follows the flow.
3. The user is then redirected to the [`AccountDetailView`](#accountdetailview) for the newly linked account.

### `AccountCreateView`

::: post_later.views.social_accounts.AccountCreateView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4
      

### `AccountDetailView`

::: post_later.views.social_accounts.AccountDetailView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4
      
### `AccountDeleteView`

::: post_later.views.social_accounts.AccountDeleteView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4
      
### `AccountListView`

::: post_later.views.social_accounts.AccountListView
    handler: python
    options:
      show_root_toc_entry: false
      heading_level: 4

## Mastodon Account Management

The flow for linking a new Mastodon account is as follows.

1. The user navigates to [`MastodonAccountAddView`](#mastodonaccountaddview) and is prompted to enter the URL for their Mastodon instance.
2. Post Later either retrieves an existing client for that instance, or creates a new one, and then redirects to that instances OAuth Authorization page.
3. The Mastodon instance then redirects the user to [`HandleMastodonAuthView`](#handlemastodonauthview) which saves the OAuth token and redirects to [`MastodonLoginView`](#mastodonloginview).
4. [`MastodonLoginView`](#mastodonloginview) sends a request for an auth token from the Mastodon instance and saves it. At this point, the account is fully authorized, and it submits a request for screenname and avatar information to save accordingly. This should also trigger the async fetch of the cached avatar file, but this is **not implemented yet**.
5. The user is then redirected to [`AccountDetailView`](#accountdetailview).

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
