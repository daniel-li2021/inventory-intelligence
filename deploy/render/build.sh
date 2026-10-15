#!/usr/bin/env bash
set -euo pipefail

# Build from clean sources so Render's cache cannot retain obsolete hashed assets.
python -m pip install --disable-pip-version-check pip==25.2 setuptools==80.9.0 wheel==0.45.1
wheel_dir=$(mktemp -d)
trap 'rm -rf "$wheel_dir"' EXIT
python scripts/build_product_wheel.py --output-dir "$wheel_dir"
python -m pip install --disable-pip-version-check --requirement deploy/lab/requirements.txt
python -m pip install --disable-pip-version-check --force-reinstall --no-deps "$wheel_dir"/*.whl
python scripts/check_product_package.py
