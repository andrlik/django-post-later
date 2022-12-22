import rules


@rules.predicate
def is_mastodon_user(user, obj):
    """
    Returns true if the object is owned by the user.
    """

    return obj.user == user


@rules.predicate
def is_valid_user(user, obj):  # pragma: nocover
    """
    Convenience method to confirm if they are an authenticated user.
    """

    return rules.is_authenticated
