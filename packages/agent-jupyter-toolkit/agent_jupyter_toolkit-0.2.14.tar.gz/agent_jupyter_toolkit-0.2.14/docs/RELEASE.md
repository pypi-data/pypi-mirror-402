# Release Process

To publish a new release to PyPI:

1. Ensure all changes are committed and tests pass:
    ```sh
    uv run pytest
    ```

2. (Recommended) Lint and format before release:
    ```sh
    uv venv .venv
    source .venv/bin/activate

    # install your package in editable mode with dev tools
    uv pip install -e ".[dev]"

    # ruff: lint + fix
    ruff check src tests --fix

    # black: format
    black src tests
    ```

3. Create and push an **annotated tag** for the release:
    ```sh
    git tag -a v0.1.2 -m "Release 0.1.2"
    git push origin v0.1.2
    ```

4. Checkout the tag to ensure you are building exactly from it:
    ```sh
    git checkout v0.1.2
    ```

5. Clean old build artifacts:
    ```sh
    rm -rf dist
    rm -rf build
    rm -rf src/*.egg-info
    ``` 

6. Upgrade build and upload tools:
    ```sh
    uv run python -m pip install --upgrade build twine packaging setuptools wheel setuptools_scm
    ```

7. Build the package:
    ```sh
    uv run python -m build
    ```

8. (Optional) Check metadata:
    ```sh
    uv run python -m twine check dist/*
    ```

9. Upload to PyPI:
    ```sh
    uv run python -m twine upload dist/*
    ```

Notes:
- Twine ≥ 6 and packaging ≥ 24.2 are required for modern metadata support.
- Always build from the tag (`git checkout vX.Y.Z`) so setuptools_scm resolves the exact version.
- `git checkout v0.1.2` puts you in detached HEAD mode; that’s normal. When done, return to your branch with:
    ```sh
    git switch -
    ```
- If you’re building in CI, make sure tags are fetched:
    ```sh
    git fetch --tags --force --prune
    git fetch --unshallow || true
    ```
