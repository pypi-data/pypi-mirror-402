# How to Upload 'checkpaste' to PyPI

This guide details the steps to build your Python package and upload it to the Python Package Index (PyPI) so others can install it via `pip install checkpaste`.

## Prerequisites

Ensure you have the necessary tools installed:

```bash
pip install build twine
```

## Step 1: Prepare Your Account

1.  **Register on PyPI**: Go to [https://pypi.org/account/register/](https://pypi.org/account/register/) and create an account.
2.  **Enable 2FA**: PyPI requires Two-Factor Authentication.
3.  **Create an API Token**:
    *   Go to **Account Settings** > **API Tokens**.
    *   Click **Add API Token**.
    *   Name it (e.g., "checkpaste-upload").
    *   Select "Entire account" (for the first upload) or scope it to the project if it already exists.
    *   **Copy the token**. It starts with `pypi-`. You will use this as your password when uploading.

## Step 2: Verify `pyproject.toml`

Ensure your `pyproject.toml` has the correct metadata. Important fields are:
*   `name`: Must be unique on PyPI. Check if 'pypaste' is taken. If it is, rename it (e.g., `pypaste-mb`).
*   `version`: `0.1.0` (increment this for every new release).
*   `authors`, `description`, `readme`.

## Step 3: Build the Package

Open your terminal in the project root (where `pyproject.toml` is) and run:

```bash
python -m build
```

This will create a `dist/` folder containing two files:
*   `pypaste-0.1.0.tar.gz` (Source Archive)
*   `pypaste-0.1.0-py3-none-any.whl` (Wheel)

## Step 4: Check the Package (Optional but Recommended)

Use `twine` to check if the description will render correctly on PyPI:

```bash
twine check dist/*
```

## Step 5: Upload to TestPyPI (Staging)

It's good practice to upload to TestPyPI first to ensure everything looks right without cluttering the real PyPI.

1.  Register at [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/).
2.  Upload:
    ```bash
    twine upload --repository testpypi dist/*
    ```
3.  You will be prompted for username (`__token__`) and password (your TestPyPI API token).

## Step 6: Upload to Real PyPI

If everything looks good, upload to the real index:

```bash
twine upload dist/*
```

1.  **Username**: `__token__`
2.  **Password**: Your PyPI API Token (starting with `pypi-...`).

## Step 7: Verify Installation

Once uploaded, anyone can install it:

```bash
pip install pypaste
```

(Note: simple names like `pypaste` might be taken. If so, change the `name` in `pyproject.toml` to something unique like `pypaste-local-sync` and rebuild).
