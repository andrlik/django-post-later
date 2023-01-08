# Displays output of `just --list`
default:
  just --list

# Downloads and installs poetry.
poetry-download:
  curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) -

# Uninstalls poetry
poetry-remove:
  curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) - --uninstall

# Installs python dependencies and mypy types.
_install:
  poetry install
  poetry run mypy --install-types --non-interactive ./

# Installs pre-commit hooks in local repo.
_pre-commit-install:
  poetry run pre-commit install

# Installs dependencies and mypy types and installs pre-commit hooks.
setup: _install _pre-commit-install

# Open django shell_plus instance.
console:
  poetry run python manage.py shell_plus

# Start up development server.
server:
  poetry run python manage.py runserver

# Rsync python environment with dependencies and run db migrations.
update: _install
  poetry run python manage.py migrate

# Run code style formatters pyupgrade, isort, and black.
codestyle:
  poetry run pyupgrade --exit-zero-even-if-changed --py39-plus **/*.py
  poetry run isort --settings-path pyproject.toml ./
  poetry run black --config pyproject.toml ./

# Run isort, black, and darglint in check-only mode.
check-codestyle:
  poetry run isort --diff --check-only --settings-path pyproject.toml ./
  poetry run black --diff --check --config pyproject.toml ./
  poetry run darglint --verbosity 2 post_later tests

# Run mkdocs to see if it is successful.
docs:
  poetry run mkdocs build

# Run mkdocs and start a liveserver.
docs-serve:
  poetry run mkdocs serve

# Deploy docs to GH Pages.
docs-deploy:
  poetry run mkdocs gh-deploy

# Runs mypy type-checking.
mypy:
  poetry run mypy --config-file pyproject.toml ./

# Runs test suite.
test:
  poetry run pytest -c pyproject.toml

# Runs poetry safety checks and bandit checks.
check-safety:
  poetry check
  poetry run safety check --full-report
  poetry run bandit -ll --recursive django-post-later tests

# Runs test suite, check-codestyle, mypy, and safety checks.
lint: test check-codestyle mypy check-safety

# Runs test suite in format suitable for CI
_citest:
  poetry run pytest --cov-report=
  poetry run coverage lcov

cisetup: _install

# Do tests and linting for CI environment.
cibuild: update _citest check-codestyle mypy check-safety

# Removes pycache directories and files.
_pycache-remove:
  find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

# Removes generated builds and dist files.
_build-remove:
  -rm -rf build/
  -rm -rf dist/

# Clean up pycache files/dirs and generated builds.
clean: _pycache-remove _build-remove
