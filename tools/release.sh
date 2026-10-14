#!/usr/bin/env bash
# Build, tag and release a version to GitHub, and optionally publish to Thunderstore.
#
# Usage: tools/release.sh X.Y.Z [--publish]
#
# Before running:
#   - Bump the version in SunThroughGrates.csproj, Plugin.cs and thunderstore.toml
#   - Move the [Unreleased] CHANGELOG.md entries under a "## [X.Y.Z] - YYYY-MM-DD" heading
#   - Commit everything; the working tree must be clean and on main
#
# Needs: dotnet, tcli (dotnet tool install -g tcli), gh (authenticated),
# VALHEIM_INSTALL (see README). --publish also needs TCLI_AUTH_TOKEN, a
# Thunderstore service account token for the nickweedon team.
set -euo pipefail

VERSION="${1:-}"
PUBLISH="${2:-}"
cd "$(dirname "$0")/.."

die() { echo "error: $*" >&2; exit 1; }

[[ "$VERSION" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] \
  || die "version must be MAJOR.MINOR.PATCH (Thunderstore doesn't accept pre-release suffixes)"
[[ -z "$PUBLISH" || "$PUBLISH" == "--publish" ]] || die "unknown option: $PUBLISH"
TAG="v$VERSION"

# Repo state
[[ "$(git branch --show-current)" == "main" ]] || die "not on main"
[[ -z "$(git status --porcelain)" ]] || die "working tree not clean"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "tag $TAG already exists"

# Version consistency
grep -q "<Version>$VERSION</Version>" SunThroughGrates/SunThroughGrates.csproj \
  || die "SunThroughGrates.csproj <Version> is not $VERSION"
grep -q "PluginVersion = \"$VERSION\"" SunThroughGrates/Plugin.cs \
  || die "Plugin.PluginVersion is not $VERSION"
grep -q "^versionNumber = \"$VERSION\"" thunderstore.toml \
  || die "thunderstore.toml versionNumber is not $VERSION"
grep -q "^## \[$VERSION\]" CHANGELOG.md || die "CHANGELOG.md has no ## [$VERSION] section"

# Build and package
dotnet build SunThroughGrates/SunThroughGrates.csproj -c Release
rm -rf build
tcli build
ZIP="build/nickweedon-SunThroughGrates-$VERSION.zip"
[[ -f "$ZIP" ]] || die "expected $ZIP from tcli build"
DLL=SunThroughGrates/bin/Release/SunThroughGrates.dll

# Release notes = this version's CHANGELOG section
NOTES="$(mktemp)"
awk -v v="$VERSION" '
  $0 ~ "^## \\[" v "\\]" { on = 1; next }
  on && /^## \[/ { exit }
  on && /^\[.*\]: / { exit }
  on { print }
' CHANGELOG.md > "$NOTES"

git tag -a "$TAG" -m "SunThroughGrates $VERSION"
git push origin "$TAG"
gh release create "$TAG" "$ZIP" "$DLL" --title "SunThroughGrates $VERSION" --notes-file "$NOTES" --verify-tag
rm -f "$NOTES"

if [[ "$PUBLISH" == "--publish" ]]; then
  [[ -n "${TCLI_AUTH_TOKEN:-}" ]] || die "TCLI_AUTH_TOKEN not set; GitHub release done, Thunderstore skipped"
  tcli publish --file "$ZIP" --token "$TCLI_AUTH_TOKEN"
fi

echo "Released $TAG"
