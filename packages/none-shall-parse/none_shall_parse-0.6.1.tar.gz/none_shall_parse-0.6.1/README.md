# none-shall-parse

A collection of shared utilities for Trinity projects.

Originally intended to be parsing utilities only, this grew to include
other useful functions.

Named for its author Andries Niemandt — whose surname loosely
translates to "none". Combined this with our parsing intentions
to create a name which nods to the Black Knight in Monty Python's Holy Grail.
https://www.youtube.com/watch?v=zKhEw7nD9C4

## Installation

Using `uv`:

```bash
uv add none-shall-parse
```

Using `pip` with `uv`:

```bash
uv pip install none-shall-parse
```

Using `pip`:

```bash
pip install none-shall-parse
```

## Development Quick Start

#### To build and publish to pypi:

Update the version in the `pyproject.toml` file, then:
```bash
uv sync --upgrade --all-extras --all-groups
pytest
rm -rf dist/ build/ *.egg-info/
uv build
uv publish
```