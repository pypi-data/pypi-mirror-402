#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/release.sh <version> [--publish] [--remote <name>]

Creates a git tag and GitHub Release from CHANGELOG.md notes.

Args:
  <version>         Version like 1.3.1 (leading "v" is ok)

Options:
  --publish         Run "uv build" and "uv publish" after creating the release
  --remote <name>   Git remote to push the tag (default: origin)
EOF
}

die() {
  echo "release.sh: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

version=""
remote="origin"
do_publish="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --publish)
      do_publish="true"
      ;;
    --remote)
      shift
      [[ $# -gt 0 ]] || die "Missing value for --remote"
      remote="$1"
      ;;
    -*)
      die "Unknown option: $1"
      ;;
    *)
      if [[ -z "$version" ]]; then
        version="$1"
      else
        die "Unexpected argument: $1"
      fi
      ;;
  esac
  shift
done

[[ -n "$version" ]] || { usage; exit 1; }

version="${version#v}"
tag="v$version"

require_cmd git
require_cmd rg
require_cmd gh
if [[ "$do_publish" == "true" ]]; then
  require_cmd uv
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  die "Working tree has uncommitted changes"
fi

project_version="$(rg -n '^version = ' pyproject.toml | sed -E 's/.*\"([^\"]+)\".*/\1/' | head -n 1)"
[[ -n "$project_version" ]] || die "Could not read version from pyproject.toml"
[[ "$project_version" == "$version" ]] || die "pyproject.toml version ($project_version) does not match $version"

rg -n "^## \\[$version\\]" CHANGELOG.md >/dev/null || die "Missing CHANGELOG section for $version"

notes="$(awk "/^## \\[$version\\]/{flag=1;next}/^## \\[/{flag=0}flag" CHANGELOG.md)"
notes_compact="$(printf "%s" "$notes" | tr -d '[:space:]')"
[[ -n "$notes_compact" ]] || die "CHANGELOG section for $version is empty"

if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
  die "Tag $tag already exists"
fi

git tag "$tag"
git push "$remote" "$tag"

printf "%s\n" "$notes" | gh release create "$tag" -t "$tag" -F - --verify-tag

if [[ "$do_publish" == "true" ]]; then
  uv build
  uv publish
fi
