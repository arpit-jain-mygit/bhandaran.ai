#!/usr/bin/env bash
# ---------------------------------------------------------------
# Builds backend/dist/lambda.zip for AWS Lambda (Python 3.14, arm64).
#
# Libraries with compiled code (psycopg, pydantic-core) must match
# Lambda's Linux + ARM CPU, not your Mac, so pip downloads the
# Linux arm64 wheels explicitly. uvicorn (local server) and alembic
# (migrations run from a laptop/CI, never from Lambda) are left out.
#
# Usage (from backend/):  ./scripts/build_lambda.sh
# ---------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."
BUILD_DIR=build/lambda
ZIP_PATH=dist/lambda.zip

# Start from a clean folder every time.
rm -rf "$BUILD_DIR" "$ZIP_PATH"
mkdir -p "$BUILD_DIR" dist

# Read runtime dependencies from pyproject.toml (minus uvicorn, alembic).
python3 - > build/requirements-lambda.txt <<'PY'
import tomllib
deps = tomllib.load(open("pyproject.toml", "rb"))["project"]["dependencies"]
skip = ("uvicorn", "alembic")
print("\n".join(d for d in deps if not d.startswith(skip)))
PY

# Download Linux arm64 wheels for Python 3.14 into the build folder.
# Two platform tags: older libraries publish "manylinux2014", newer
# ones (psycopg 3.3) "manylinux_2_28"; Lambda (Amazon Linux 2023,
# glibc 2.34) can run both.
python3 -m pip install \
  --quiet \
  --target "$BUILD_DIR" \
  --platform manylinux2014_aarch64 \
  --platform manylinux_2_28_aarch64 \
  --implementation cp \
  --python-version 3.14 \
  --only-binary=:all: \
  -r build/requirements-lambda.txt

# Add our own code.
cp -r app "$BUILD_DIR/"

# Drop caches to keep the zip small, then zip.
find "$BUILD_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} +
(cd "$BUILD_DIR" && zip -qr9 "../../$ZIP_PATH" .)

echo "Built $ZIP_PATH ($(du -h "$ZIP_PATH" | cut -f1))"
