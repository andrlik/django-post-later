import rules


@rules.predicate
def is_owner(user, obj):
    return obj.user == user


@rules.predicate
def is_mastodon_avatar_owner(user, obj):
    return obj.user_account.user == user


@rules.predicate
def is_valid_user(user, obj):  # pragma: nocover
    return rules.is_authenticated
