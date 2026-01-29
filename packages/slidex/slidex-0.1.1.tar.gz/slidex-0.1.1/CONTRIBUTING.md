# Contributing to slidex

Thanks for helping build slidex. This guide focuses on developer setup,
tooling, and project conventions.

## Prerequisites

- Python 3.9+
- Rust toolchain (stable)
- `uv` for Python dependency management

## Development setup (uv)

```bash
uv venv
uv pip install -e .[dev]
uv run maturin develop
```

## Git hooks (optional)

Enable the local git hooks to keep `pyproject.toml` in sync with the version
in `Cargo.toml`:

```bash
git config core.hooksPath .githooks
```

## Running tests

All tests (Rust + Python):

```bash
uv run -s scripts/test_all.py
```

Python tests:

```bash
uv run -s scripts/test_python.py
```

Rust tests (core only):

```bash
cargo test
```

## Fixture generation (dev-only)

Fixtures are generated via a separate tool subproject that depends on
`python-pptx` but is not required by the library itself.

```bash
cd tools/fixture_gen
python -m venv .venv
source .venv/bin/activate
pip install -e .
python generate_fixtures.py
```

This also produces a template PPTX used by `Presentation.new()` when available.

## Fixture comparison (dev-only)

Use the comparison script to validate generated output against a golden deck.

```bash
python tools/fixture_compare/compare_pptx.py \
  tests/fixtures/generated/simple/title_and_content.pptx \
  path/to/output.pptx
```

## Project layout

- `src/` Rust core and PyO3 module
- `python/slidex/` Python package and stubs
- `docs/` design and architecture docs
- `tests/` Rust and Python tests
- `tools/` dev-only tooling (fixture generation/comparison)

## Style

- Keep changes small and focused.
- Add or update tests when behavior changes.
- Prefer ASCII in source files unless required.

## Publishing to PyPI (maintainers)

1. Create a PyPI API token at https://pypi.org/manage/account/token/
2. Add the token as a GitHub repository secret named `PYPI_API_TOKEN`.
3. Bump the version in `Cargo.toml`.
4. Commit and push the change (the pre-commit hook syncs `pyproject.toml`):
   ```bash
   git add Cargo.toml pyproject.toml
   git commit -m "Bump version to vX.Y.Z"
   git push origin main
   ```
5. Create a published release (also creates the tag) using the version:
   ```bash
   gh release create vX.Y.Z --generate-notes
   ```
6. The `Publish` workflow will download the CI-built artifacts and upload them via `uv publish`.

Notes:
- The workflow is in `.github/workflows/publish.yml`.
- Uploads use `uv publish dist/*`.
- Artifacts are reused from the successful `CI` workflow run for the release commit.

## Pull requests

- Describe the change and rationale.
- Link to relevant issues or docs.
- Ensure CI passes.
