import rules


@rules.predicate
def is_mastodon_user(user, obj):
    return obj.user == user


@rules.predicate
def is_valid_user(user, obj):  # pragma: nocover
    return rules.is_authenticated
