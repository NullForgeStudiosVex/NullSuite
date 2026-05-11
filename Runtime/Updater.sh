#!/bin/bash

RUNTIME_DIR="$(dirname "$(realpath "$0")")"
REPO_DIR="$(dirname "$RUNTIME_DIR")"

cd "$REPO_DIR" || exit 1

echo "Updating..."
git pull

sleep 1

echo "Restarting..."
nohup "$RUNTIME_DIR/NSLauncher.sh" >/dev/null 2>&1 &

exit 0