# hangul-keyboard

A Python package for converting Roman keyboard input to Korean Hangul automatically.

## Features

- Automatic Roman → Hangul conversion
- Korean input auto-detection (returns as-is if already Hangul)
- 2-Set Korean keyboard layout support
- Double consonants/vowels support (ㄲ, ㅃ, ㄳ, etc.)
- Decompose Hangul into jamo sequences (list or string) for search and LLM preprocessing
- Perfect for search systems, autocomplete, and text analysis

## Installation

```bash
pip install hangul-keyboard
```

## Project Structure

```
hangul-keyboard/
├── hangul_keyboard/
│   ├── __init__.py
│   ├── core.py          # Core conversion logic
│   └── mapping.py       # Roman-to-Jamo mapping tables
├── tests/
│   ├── __init__.py
│   ├── test_core.py        # Unit tests for core.py
│   ├── test_mapping.py     # Unit tests for mapping.py
│   └── test_integration.py # Integration tests
├── README.md
├── setup.py (or pyproject.toml)
└── requirements.txt
```

## Quick Start

```python
from hangul_keyboard import convert_roman_to_hangul, decompose_hangul_full, decompose_hangul_str

# Basic usage
result = convert_roman_to_hangul("dkssud")
print(result)  # Output: "한글"

# Already Hangul - returns as-is
result = convert_roman_to_hangul("한글")
print(result)  # Output: "한글"

# Mixed with numbers and special characters
result = convert_roman_to_hangul("rk123!")
print(result)  # Output: "가123!"

# Decompose into jamo list (full)
jamo_list = decompose_hangul_full("한글")
print(jamo_list)  # Output: ['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ']

# Decompose into jamo string
jamo_str = decompose_hangul_str("한글")
print(jamo_str)  # Output: "ㅎㅏㄴㄱㅡㄹ"
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_core.py -v
python -m pytest tests/test_mapping.py -v
python -m pytest tests/test_integration.py -v

# Or use unittest
python -m unittest tests.test_core -v
```