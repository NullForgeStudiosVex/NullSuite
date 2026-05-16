#!/bin/bash

FILE="$1"

if [ ! -f "$FILE" ]; then
    exit 1
fi

DIR="$(dirname "$FILE")"
FILENAME="$(basename "$FILE")"
NAME="${FILENAME%.*}"

TARGET="$DIR/$NAME"

mkdir -p "$TARGET"

7z x "$FILE" -o"$TARGET"
