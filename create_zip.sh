#!/bin/sh
set -eu

REPO_DIR="$(pwd)"
rm -f "$REPO_DIR/rbfa.zip"

(
    cd custom_components/rbfa

    zip "$REPO_DIR/rbfa.zip" \
        *.py \
        manifest.json \
        translations/*.json \
        brand/icon.png
)