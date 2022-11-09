=================
Django Post Later
=================


[![PyPI version](https://img.shields.io/pypi/v/django-post-later.svg)](https://pypi.python.org/pypi/django-post-later)

[![BSD](https://img.shields.io/github/license/andrlik/django-post-later)](https://github.com/andrlik/django-post-later/blob/main/LICENSE)

[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

[![Pre-commit enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/andrlik/django-post-later/blob/main/.pre-commit-config.yaml)

[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)

[![Semantic versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/andrlik/django-post-later/releases)

[![Build status badge](https://github.com/andrlik/django-post-later/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/andrlik/django-post-later/actions/workflows/test.yml)

[![Codestyle test status](https://github.com/andrlik/django-post-later/actions/workflows/codestyle.yml/badge.svg?branch=main)](https://github.com/andrlik/django-post-later/actions/workflows/codestyle.yml)



[![Code coverage badge](https://coveralls.io/repos/github/andrlik/django-post-later/badge.svg?branch=main)](https://coveralls.io/github/andrlik/django-post-later?branch=main)




[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://andrlik.github.io/django-post-later/)

A simple django app for scheduling posts for Twitter, Mastodon, and others.


* Free software: BSD
* Repository and Issue Tracker: https://github.com/andrlik/django-post-later/
* Documentation: https://django-post-later.readthedocs.io.


## Features

- TODO

## Developing

If you don't already have poetry installed on your system, you can use:

```bash
$ just poetry-download
```

Then install all the dependencies:

```bash
$ just setup
```

Run codestyle:

```bash
$ just codestyle
```

If you want to run safety checks:

```bash
$ just check-safety
```

If you want to run tests:

```bash
$ just test
```

If you want to check types:

```bash
$ just mypy
```

If you want to check everything:

```bash
$ just lint
```

In order to submit a pull request, it is expected that you've written tests and documentation for your changes,
and that running `just lint` passes without issue.

## Credits

This package was created with [Cookiecutter][cc] and the [`andrlik/cookiecutter-poetry-djangopackage`][acpd] template.

[cc]: https://github.com/audreyr/cookiecutter
[acpd]: https://github.com/andrlik/cookiecutter-poetry-djangopackage
