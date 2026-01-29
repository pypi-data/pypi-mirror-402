#!/usr/bin/env bash
set -euo pipefail

PY_VERSIONS=${PY_VERSIONS:-"3.10 3.11 3.12 3.13 3.14"}

for version in $PY_VERSIONS; do
  echo "==> Python $version"
  uv run --python "$version" --with pytest -- pytest "$@"
done
