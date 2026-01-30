# PromptShield (pshield)

A Python library that automatically detects and replaces sensitive information in text with placeholders.

## Features

- 🔒 Detects 20+ entity types (emails, phones, cards, names, locations, etc.)
- 🌍 Multi-language support with automatic placeholder translation
- 🎯 Uses spaCy NER for accurate name/location detection
- 🔄 Consistent placeholders across documents

## Installation

```bash
pip install pshield
python -m spacy download en_core_web_sm
```

## Quick Start

```python
from pshield import PromptShield

shield = PromptShield()
protected = shield.protect("John sent $50 to jane@example.com")
# Output: "[NAME_1] sent [AMOUNT_1] to [EMAIL_1]"
```

## Usage

```python
# Disable translation (keep placeholders in English)
protected = shield.protect("Your text", translate=False)

# Multi-language example
shield.protect("Bob a envoyé 50 USD à bob@example.com")
# Returns: "[NOM_1] a envoyé [MONTANT_1] à [E-MAIL_1]"
```

## Supported Entities

**Personal**: Names, emails, phones, usernames  
**Financial**: Credit cards, CVV, expiry dates, amounts  
**Location**: Places, coordinates, IP addresses  
**Digital**: URLs, JWT tokens, Bitcoin/Ethereum addresses  
**Other**: Dates, memory sizes, alphanumeric codes

## API

### `PromptShield(nlp=None)`

- `nlp`: Optional spaCy model (defaults to `en_core_web_sm`)

### `protect(text: str, translate: bool = True) -> str`

Replaces sensitive entities with placeholders.

- `text`: Input text to protect
- `translate`: Translate placeholders to detected language (default: `True`)

## Requirements

Python 3.9+, spaCy >= 3.7.0, langdetect >= 1.0.9, deep-translator >= 1.11.4

## Links

- **GitHub**: https://github.com/adiletbaimyrza/promptshield
- **PyPI**: https://pypi.org/project/pshield/

## License

MIT
