"""
PyHanNom: Vietnamese Latin ↔ Han-Nom converter and lookup tool
"""
## 0.1.3 functions
from .load_syllable_char_table import load_syllable_char_table
from .get_chuhannom_from_latin import (
    get_chuhannom_from_latin,
    get_chuhannom_unicode_from_latin,
)
from .get_latin_from_chuhannom import get_latin_from_chuhannom

from .load_word_table import load_word_table
from .get_chuhannom_word_from_latin import get_chuhannom_word_from_latin
from .get_latin_word_from_chuhannom import get_latin_word_from_chuhannom

## 0.2.0 functions
from .load_hannom_table import load_hannom_table
from .latin_to_hannom import latin_to_hannom
from .hannom_to_latin import hannom_to_latin
from .load_parallel_corpus import load_parallel_corpus

__version__ = "0.2.0"

__all__ = [
    "load_syllable_char_table",
    "get_chuhannom_from_latin",
    "get_chuhannom_unicode_from_latin",
    "get_latin_from_chuhannom",
    "load_word_table",
    "get_chuhannom_word_from_latin",
    "get_latin_word_from_chuhannom",
    "load_hannom_table",
    "latin_to_hannom",
    "hannom_to_latin",
    "load_parallel_corpus"
]
