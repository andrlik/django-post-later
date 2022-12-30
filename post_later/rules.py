import rules


@rules.predicate
def is_owner(user, obj):
    """
    Returns true if the object is owned by the user.
    """

    return obj.user == user


@rules.predicate
def is_mastodon_avatar_owner(user, obj):
    """
    Returns true if the avatar is owned by the user.
    """

    return obj.user_account.user == user


@rules.predicate
def is_valid_user(user, obj):  # pragma: nocover
    """
    Convenience method to confirm if they are an authenticated user.
    """

    return rules.is_authenticated


@rules.predicate
def is_social_content_owner(user, obj):
    """
    Checks to ensure the user is also the owner of
    the associated account.
    """

    return obj.account.user == user
