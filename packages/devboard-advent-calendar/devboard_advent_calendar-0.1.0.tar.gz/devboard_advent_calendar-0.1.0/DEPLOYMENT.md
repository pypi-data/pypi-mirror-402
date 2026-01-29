# Deploying DevBoard to PyPI / TestPyPI

## Prerequisites

1. **Update `pyproject.toml`**:
   - Replace `"Your Name"` and `"your.email@example.com"` with your actual name and email in the `[project]` section

2. **Install required tools**:
   ```bash
   # PowerShell or Command Prompt
   py -m pip install build twine
   
   # Or if pip is in PATH:
   pip install build twine
   ```

3. **Create PyPI/TestPyPI account**:
   - For TestPyPI: https://test.pypi.org/account/register/
   - For PyPI: https://pypi.org/account/register/
   
4. **Generate API tokens**:
   - TestPyPI: Go to https://test.pypi.org/manage/account/#api-tokens
   - PyPI: Go to https://pypi.org/manage/account/#api-tokens
   - Create a new API token (scope: "Entire account" for simplicity)
   - Save the token (starts with `pypi-`)

## Building the Package

1. **Clean previous builds** (if any):
   ```powershell
   # PowerShell:
   Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
   ```
   ```cmd
   # Command Prompt (cmd.exe):
   if exist dist rmdir /s /q dist
   if exist build rmdir /s /q build
   for /d %i in (*.egg-info) do @rmdir /s /q "%i"
   ```

2. **Build the distribution packages**:
   ```bash
   py -m build
   # or
   python -m build
   ```

   This creates:
   - `dist/devboard-0.1.0.tar.gz` (source distribution)
   - `dist/devboard-0.1.0-py3-none-any.whl` (wheel distribution)
   
   **Note**: Package names are normalized to lowercase by PyPI, so "DevBoard" becomes "devboard".

## Uploading to TestPyPI (Recommended First Step)

1. **Upload using twine**:
   ```bash
   py -m twine upload --repository testpypi dist/*
   # or
   python -m twine upload --repository testpypi dist/*
   ```

2. **When prompted**:
   - Username: `__token__`
   - Password: Your TestPyPI API token (including the `pypi-` prefix)

3. **Verify the upload**:
   - Check: https://test.pypi.org/project/devboard/

4. **Test installation from TestPyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ devboard
   ```

## Uploading to Production PyPI

⚠️ **Important**: Only upload to production PyPI after testing on TestPyPI!

1. **Update version number** (if needed):
   - Edit `version = "0.1.0"` in `pyproject.toml` for each release

2. **Rebuild** (if version changed):
   ```bash
   py -m build
   # or
   python -m build
   ```

3. **Upload to PyPI**:
   ```bash
   py -m twine upload dist/*
   # or
   python -m twine upload dist/*
   ```

4. **When prompted**:
   - Username: `__token__`
   - Password: Your PyPI API token (including the `pypi-` prefix)

5. **Verify the upload**:
   - Check: https://pypi.org/project/devboard/

## After Publishing

Users can install your package with:
```bash
pip install devboard
# Note: PyPI normalizes package names to lowercase
```

And run it with:
```bash
advent-calendar
```

## Common Issues

- **403 Forbidden**: Check your API token and ensure it has the correct scope
- **400 Bad Request**: Package name might already exist. Try a different name or increment version
- **Duplicate package**: Wait a few minutes between uploads, or increment the version number
- **Package name normalization**: PyPI converts package names to lowercase, so "DevBoard" becomes "devboard" in the distribution files
- **Windows PATH issues**: If `pip` or `python` commands aren't recognized, use `py -m pip` or `py -m python` instead

## Security Note

Never commit your API tokens to version control! Store them securely or use environment variables.

