#!/usr/bin/env bash

set -euo pipefail

PYTHON_VERSIONS=(3.12 3.13 3.14)
WAGTAIL_VERSIONS=(">=6,<7" ">=7,<8")

echo "Type Check:"
echo "==========="
uv run --group=dev ty check lazy_streamfield/
echo ""

echo "Test Matrix:"
echo "============"
for python in "${PYTHON_VERSIONS[@]}"; do
    for wagtail in "${WAGTAIL_VERSIONS[@]}"; do
        echo "  Python ${python} + Wagtail ${wagtail}"
    done
done
echo ""

for python in "${PYTHON_VERSIONS[@]}"; do
    for wagtail in "${WAGTAIL_VERSIONS[@]}"; do
        uv run --no-project --python="${python}" --with="wagtail${wagtail}" --with=pytest --with=pytest-django --with=. \
            pytest tests/
    done
done
