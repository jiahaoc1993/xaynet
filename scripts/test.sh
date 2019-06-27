#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $DIR/../

# sort import
isort --check-only --indent=4 -rc setup.py autofl && echo "===> isort says: well done <===" &&

# format code
black --check setup.py autofl && echo "===> black says: well done <===" &&

# lint
pylint --rcfile=pylint.ini autofl && echo "===> pylint says: well done <===" &&

# type checks
mypy --ignore-missing-imports autofl && echo "===> mypy says: well done <===" &&

# tests
pytest -v -m unmarked && echo "===> pytest/unmarked says: well done <==="
pytest -v -m integration && echo "===> pytest/integration says: well done <==="
