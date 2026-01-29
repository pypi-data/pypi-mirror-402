# Manual Release Checklist

This project uses `CHANGELOG.md`, git tags, and GitHub Releases.
PyPI publishing is still done with `uv build` and `uv publish`.

## 1) Update version + changelog

```bash
rg -n '^version = ' pyproject.toml
```

Edit `pyproject.toml` to the new version, and add a section in `CHANGELOG.md`:

```
## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

Move any items from `Unreleased` into the new version section.

## 2) Commit the release metadata

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to X.Y.Z"
```

## 3) Tag and push the release

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

## 4) Create the GitHub Release (gh CLI)

```bash
NOTES=$(awk '/^## \\[X.Y.Z\\]/{flag=1;next}/^## \\[/{flag=0}flag' CHANGELOG.md)
gh release create vX.Y.Z -t "vX.Y.Z" -n "$NOTES"
```

## 5) Publish to PyPI

```bash
uv build
uv publish
```
