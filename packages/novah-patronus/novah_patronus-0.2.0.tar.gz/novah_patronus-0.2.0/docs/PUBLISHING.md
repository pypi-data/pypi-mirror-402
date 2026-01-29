# Publishing novah-patronus to PyPI

This document describes how to publish `novah-patronus` to PyPI using Trusted Publishing (OIDC).

## Overview

The package is published to [PyPI](https://pypi.org) using GitHub Actions with **Trusted Publishing**. This modern approach uses OpenID Connect (OIDC) tokens instead of API tokens, providing better security and no secrets to manage.

## Prerequisites

- PyPI account with access to the `novah-patronus` package (or create it on first publish)
- GitHub repository admin access
- Package version updated in `pyproject.toml`

## One-Time Setup

### 1. Configure Trusted Publisher on PyPI

1. Go to [https://pypi.org](https://pypi.org) and sign in
2. Navigate to your account > **Publishing** tab
3. Click **Add a new pending publisher** (for first-time setup) or go to the package settings
4. Fill in the Trusted Publisher details:
   - **PyPI Project Name**: `novah-patronus`
   - **Owner**: `Novah-Care`
   - **Repository name**: `patronus`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
5. Click **Add**

### 2. Create GitHub Environment

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Environments**
3. Click **New environment**
4. Name it `pypi` (must match the workflow)
5. Optionally configure protection rules:
   - **Required reviewers**: Add team members who must approve deployments
   - **Deployment branches**: Restrict to `main` or release tags

## Publishing a New Version

### 1. Update Version

Edit `pyproject.toml` and update the version number:

```toml
[project]
name = "novah-patronus"
version = "0.2.0"  # Update this
```

### 2. Create a GitHub Release

1. Go to **Releases** > **Draft a new release**
2. Click **Choose a tag** and create a new tag (e.g., `v0.2.0`)
3. Set the release title (e.g., `v0.2.0`)
4. Add release notes describing changes
5. Click **Publish release**

The workflow will automatically:
- Build the package
- Upload to PyPI using Trusted Publishing

### 3. Manual Trigger (Optional)

You can also trigger the workflow manually:

1. Go to **Actions** > **Publish to PyPI**
2. Click **Run workflow**
3. Select the branch and click **Run workflow**

## Verifying the Release

After the workflow completes:

1. Check the [Actions tab](https://github.com/Novah-Care/patronus/actions) for workflow status
2. Verify the package on [PyPI](https://pypi.org/project/novah-patronus/)
3. Test installation:
   ```bash
   pip install novah-patronus
   ```

## Installing the Package

### With pip

```bash
pip install novah-patronus
```

### With Poetry

```bash
poetry add novah-patronus
```

Or add to `pyproject.toml`:

```toml
[tool.poetry.dependencies]
novah-patronus = "^0.2.0"
```

## Troubleshooting

### "Trusted publishing is not configured"

Ensure the Trusted Publisher is configured on PyPI with exactly matching values:
- Repository owner: `Novah-Care`
- Repository name: `patronus`
- Workflow filename: `publish.yml`
- Environment name: `pypi`

### "Permission denied" errors

1. Verify the `pypi` environment exists in GitHub repository settings
2. Check that the workflow has `id-token: write` permission
3. Ensure you have maintainer/owner access to the PyPI project

### Build failures

Test the build locally first:

```bash
pip install build
python -m build
```

Check that all required files are included and the version is valid.

## How Trusted Publishing Works

1. GitHub Actions generates a short-lived OIDC token
2. The token identifies the workflow (repository, workflow file, environment)
3. PyPI verifies the token against the configured Trusted Publisher
4. If valid, PyPI accepts the upload without requiring API tokens

This eliminates the need to store secrets in GitHub and provides better audit trails.

## References

- [PyPI Trusted Publishing documentation](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
