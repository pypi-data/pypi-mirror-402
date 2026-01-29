#!/bin/bash
VERSION="0.3.0"
MAJOR_MINOR=$(echo "$VERSION" | cut -d. -f1,2)
CHANGELOG_FILE="CHANGELOG/CHANGELOG-${MAJOR_MINOR}.md"
set -euo pipefail
[[ -f "$CHANGELOG_FILE" ]] || { echo "ERROR: $CHANGELOG_FILE not found" >&2; exit 1; }
HEADER_REGEX="^#\{1,2\} \\[${VERSION//./\\.}\\]"
SECTION=$(sed -n "/$HEADER_REGEX/,\$p" "$CHANGELOG_FILE")
[[ -n "$SECTION" ]] || { echo "ERROR: No changelog section for $VERSION in "$CHANGELOG_FILE"" >&2; exit 1; }
NEXT_VERSION=$(echo "$SECTION" | grep -m1 "^#\{1,2\} \\[[0-9]" || true)
if [[ -n "$NEXT_VERSION" ]]; then
    CHANGELOG=$(echo "$SECTION" | sed '1d' | sed '/^#\{1,2\} \[[0-9]/,$d')
else
    CHANGELOG=$(echo "$SECTION" | sed '1d')
fi
[[ -n "$CHANGELOG" ]] || { echo "ERROR: Empty changelog body for $VERSION in "$CHANGELOG_FILE"" >&2; exit 1; }
{
echo "changelog<<EOF"
echo "$CHANGELOG"
echo "EOF"
}
