#!/bin/bash

BASE_DIR="$(dirname "$(realpath "$0")")"
CONFIG="$BASE_DIR/NullSuite.json"

# ------------------------------
# Check config exists
# ------------------------------
if [ ! -f "$CONFIG" ]; then
    echo "❌ NullSuite.json not found"
    read -p "Press enter to exit..."
    exit 1
fi

# ------------------------------
# Extract Proton path
# ------------------------------
PROTON=$(python3 -c "
import json,sys

try:
    data = json.load(open('$CONFIG'))
    print(data['NullProton']['Default'])
except Exception:
    sys.exit(1)
")

# ------------------------------
# Validate Proton path
# ------------------------------
if [ -z "$PROTON" ] || [ "$PROTON" = "[ not set ]" ]; then
    echo "❌ Proton not set in config"
    read -p "Press enter to exit..."
    exit 1
fi

if [ ! -f "$PROTON" ]; then
    echo "❌ Proton executable not found:"
    echo "$PROTON"
    read -p "Press enter to exit..."
    exit 1
fi

# ------------------------------
# Validate game input
# ------------------------------
if [ -z "$1" ]; then
    echo "❌ No game provided"
    read -p "Press enter to exit..."
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "❌ Game not found:"
    echo "$1"
    read -p "Press enter to exit..."
    exit 1
fi

# ------------------------------
# Proton env
# ------------------------------
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.steam/steam"

GAME_NAME=$(basename "$1")
PREFIX="$BASE_DIR/ProtonDrive/Default"

mkdir -p "$PREFIX"

export STEAM_COMPAT_DATA_PATH="$PREFIX"

# ------------------------------
# Launch
# ------------------------------
echo "🚀 Launching:"
echo "$GAME_NAME"
echo
echo "Using Proton:"
echo "$PROTON"
echo
echo "Please wait... first launch can take a bit."

setsid "$PROTON" run "$1" >/dev/null 2>&1 &
echo "✅ Game started."
echo "This will close in 5s"
sleep 5
exit 0
