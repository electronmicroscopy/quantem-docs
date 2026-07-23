---
title: Contribute
---

# Contributing

quantEM is developed openly at [github.com/electronmicroscopy/quantem](https://github.com/electronmicroscopy/quantem). Bug reports, feature requests, and pull requests are welcome through GitHub issues and PRs.

## Development setup

Development uses [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/electronmicroscopy/quantem.git
cd quantem
uv sync
```

Linting and formatting use [ruff](https://github.com/astral-sh/ruff) via pre-commit:

```bash
uv tool install pre-commit
uv tool install ruff
pre-commit install
```

Tests run with pytest:

```bash
uv run pytest
```

The complete developer guide (widget development, dependency management, environment activation) is in [CONTRIBUTORS.md](https://github.com/electronmicroscopy/quantem/blob/main/CONTRIBUTORS.md).

## Contributing to the documentation

This site is written in [MyST Markdown](https://mystmd.org) and lives in the [quantem-docs](https://github.com/electronmicroscopy/quantem-docs) repository. To preview changes locally:

```bash
npm install -g mystmd
myst start
```

Tutorial notebooks live in [quantem-tutorials](https://github.com/electronmicroscopy/quantem-tutorials).
