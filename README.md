# Django Post Later

[![PyPI version](https://img.shields.io/pypi/v/django-post-later.svg)](https://pypi.python.org/pypi/django-post-later)
[![BSD](https://img.shields.io/github/license/andrlik/django-post-later)](https://github.com/andrlik/django-post-later/blob/main/LICENSE)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Pre-commit enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/andrlik/django-post-later/blob/main/.pre-commit-config.yaml)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Semantic versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/andrlik/django-post-later/releases)
[![Build status badge](https://github.com/andrlik/django-post-later/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/andrlik/django-post-later/actions/workflows/build.yml)
[![Code coverage badge](https://coveralls.io/repos/github/andrlik/django-post-later/badge.svg?branch=main)](https://coveralls.io/github/andrlik/django-post-later?branch=main)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://andrlik.github.io/django-post-later/)

A simple django app for scheduling posts for Twitter, Mastodon, and others.

* Free software: BSD
* Repository and Issue Tracker: https://github.com/andrlik/django-post-later/
* Documentation: https://andrlik.github.io/django-post-later/.


## Features

### Planned

- Authenticate to an arbitrary number of your Twitter and Mastodon accounts.
- Schedule posts to either for future dates, including media uploads.
- Schedule RTs and Boosts.
- Maybe Instagram posts? I dunno. I really hate doing anything with FB.

Includes some basic templates for each view, but the assumption is that you will likely want to customize them. To keep dependencies
manageable, we don't make any assumptions about your JS/CSS framework.

### Working

- Nothing. This project just started, yo.

## Credits

This package was created with [Cookiecutter][cc] and the [`andrlik/cookiecutter-poetry-djangopackage`][acpd] template.

[cc]: https://github.com/audreyr/cookiecutter
[acpd]: https://github.com/andrlik/cookiecutter-poetry-djangopackage
