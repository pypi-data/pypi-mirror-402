# Releasing django-issue-capture

> **Tip**: Use the `/publish` command in Claude Code to execute this workflow automatically.

## Pre-release Checklist

1. Ensure all changes are committed and pushed
2. Ensure you're on the `master` branch
3. Verify CI is passing

## Release Steps

### Step 1: Determine Version Number

- Check current version in `pyproject.toml` and `src/django_issue_capture/__init__.py`
- Follow semantic versioning: MAJOR.MINOR.PATCH
  - PATCH: Bug fixes, minor changes
  - MINOR: New features, backwards compatible
  - MAJOR: Breaking changes

### Step 2: Run Pre-release Checks

```bash
make check && make test
```

If either fails, fix issues before proceeding.

### Step 3: Update Version

Update version in both files:
- `pyproject.toml`: `version = "X.Y.Z"`
- `src/django_issue_capture/__init__.py`: `__version__ = "X.Y.Z"`

### Step 4: Commit Version Bump

```bash
git add pyproject.toml src/django_issue_capture/__init__.py
git commit -m "Bump version to X.Y.Z"
git push
```

### Step 5: Create GitHub Release

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes
```

GitHub Actions will automatically publish to PyPI.

### Step 6: Verify Release

- Check PyPI: https://pypi.org/project/django-issue-capture/
- Verify version matches
