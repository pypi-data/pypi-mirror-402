# Development Setup

## Initial Setup

1. Create virtual environment:
   ```bash
   cd packages/pip-package
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   pip install -e .
   ```

## Development

- Main class: `src/pshield/pshield.py`
- Import: `from pshield import PromptShield`
- Run tests: `pytest src/pshield/test_pshield.py`

## Publishing to PyPI

1. Update version in `pyproject.toml` (follow [Semantic Versioning](https://py-pkgs.org/07-releasing-versioning.html))

2. Install build tools:
   ```bash
   pip install build twine
   ```

3. Build and upload:
   ```bash
   python -m build
   python3 -m twine upload --repository pypi dist/*
   ```
   (Ask Adilet for PyPI API token)

4. Verify:
   ```bash
   pip install pshield --upgrade
   ```

## Troubleshooting

- **spaCy model not found**: `python -m spacy download en_core_web_sm`
- **Import errors**: `pip install -e .`
- **Build errors**: `pip install build twine`
