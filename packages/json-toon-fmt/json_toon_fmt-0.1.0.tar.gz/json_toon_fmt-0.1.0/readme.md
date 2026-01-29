
# Python Toon — JSON to TOON converter

`python-toon` converts JSON data into the TOON data format used by downstream tools.

**Author:** Naman Gupta

## What it does

- Parse and normalise JSON input into an internal TOON representation
- Intended for programmatic use in pipelines

## Install

Install for development:

```bash
python -m pip install -e .
```

Install runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

## Quick example

Conceptual example (see the package source for exact APIs):

```py
from python_toon import encode

# load JSON (from file, network, etc.)
data = {"type": "scene", "items": [...]}

# convert to TOON representation
toon_obj=encode(data)
print(toon_obj)
```

## Project layout

- `src/python_toon/normaliser.py` — JSON → TOON normalisation
- `src/python_toon/formatter.py` — formatting helpers
- `src/python_toon/writer.py` — emit TOON files
- `tests/` — unit tests (run with `pytest`)

## Tests

Run the test suite:

```bash
pytest -q
```

## Contributing

Open issues or PRs. Please include tests for new behaviors and keep changes focused.

## License

See the `license` file in the project root.
