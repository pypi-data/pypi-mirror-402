"""
Text tokenizer for stylometric analysis.

Handles unicode normalization, text cleaning, and tokenization
for vocabulary analysis.
"""

import re
from typing import Iterator


# =============================================================================
# UNICODE NORMALIZATION
# =============================================================================

# Single-character replacements via str.maketrans (O(n) single pass)
_SINGLE_CHAR_MAP: dict[int, str] = {
    # Single quotes
    0x2018: "'",  # ' Left single quotation mark
    0x2019: "'",  # ' Right single quotation mark
    0x201A: "'",  # ‚ Single low-9 quotation mark
    0x201B: "'",  # ‛ Single high-reversed-9 quotation mark
    0x2032: "'",  # ′ Prime
    0x2035: "'",  # ‵ Reversed prime
    0x0060: "'",  # ` Grave accent
    0x00B4: "'",  # ´ Acute accent
    # Double quotes
    0x201C: '"',  # " Left double quotation mark
    0x201D: '"',  # " Right double quotation mark
    0x201E: '"',  # „ Double low-9 quotation mark
    0x201F: '"',  # ‟ Double high-reversed-9 quotation mark
    0x2033: '"',  # ″ Double prime
    0x2036: '"',  # ‶ Reversed double prime
    0x00AB: '"',  # « Left-pointing double angle
    0x00BB: '"',  # » Right-pointing double angle
    # Dashes (single-char normalizations)
    0x2013: "-",  # – En dash
    0x2012: "-",  # ‒ Figure dash
    # Spaces
    0x00A0: " ",  # Non-breaking space
    0x2003: " ",  # Em space
    0x2002: " ",  # En space
    # Ligatures (OCR artifacts)
    0xFB01: "fi",  # ﬁ
    0xFB02: "fl",  # ﬂ
    0xFB00: "ff",  # ﬀ
    0xFB03: "ffi",  # ﬃ
    0xFB04: "ffl",  # ﬄ
    # Historical orthography
    0x017F: "s",  # ſ Long s
}

_UNICODE_TABLE = str.maketrans(_SINGLE_CHAR_MAP)

# Multi-character replacements (compiled alternation pattern)
_MULTI_CHAR_REPLACEMENTS: dict[str, str] = {
    "\u2014": "--",  # — Em dash
    "\u2015": "--",  # ― Horizontal bar
    "\u2026": "...",  # … Ellipsis
}

_MULTI_CHAR_PATTERN = re.compile("|".join(re.escape(k) for k in _MULTI_CHAR_REPLACEMENTS))


def _multi_char_replacer(match: re.Match) -> str:
    return _MULTI_CHAR_REPLACEMENTS[match.group(0)]


def normalize_unicode(text: str) -> str:
    """Replace smart quotes, em-dashes, ligatures, and other unicode with ASCII."""
    text = text.translate(_UNICODE_TABLE)
    text = _MULTI_CHAR_PATTERN.sub(_multi_char_replacer, text)
    return text


# =============================================================================
# TEXT CLEANING
# =============================================================================

# Italics/emphasis markers: _word_
_ITALICS_PATTERN = re.compile(r"_([^_]+)_")

# Bracketed editorial insertions: [Illustration], [Footnote 1: text], [1]
_BRACKET_PATTERN = re.compile(r"\[[^\]]*\]")

# Line-break hyphenation: "com-\nplete" → "complete"
_LINEBREAK_HYPHEN_PATTERN = re.compile(r"(\w+)-\s*\n\s*(\w+)")


def clean_text_artifacts(text: str) -> str:
    """Remove common formatting artifacts from text."""
    text = _ITALICS_PATTERN.sub(r"\1", text)
    text = _BRACKET_PATTERN.sub(" ", text)
    text = _LINEBREAK_HYPHEN_PATTERN.sub(r"\1\2", text)
    return text


# =============================================================================
# TOKEN PATTERN
# =============================================================================

# Priority-ordered alternations:
#
# 1. Apostrophe-initial contractions: 'twas, 'tis, 'twere, 'em
# 2. Internal elisions: e'er, ne'er, o'er
# 3. Hyphenated compounds with optional possessive: mother-in-law's
# 4. Standard contractions: didn't, won't, I'm, we'll
# 5. Possessives: Alice's, James's
# 6. Dialect g-dropping: runnin', somethin'
# 7. Plain words
# 8. Roman numerals: VII, XLII
# 9. Ordinals: 1st, 2nd, 3rd
# 10. Decimal numbers: 3.14, 1,000
# 11. Plain integers

_TOKEN_PATTERN = re.compile(
    r"""
    '[a-z]+                                     # 'twas, 'tis, 'em
    |
    [a-z]+'[a-z]+                               # e'er, ne'er, o'er
    |
    [a-z]+(?:-[a-z]+)+(?:'s)?                   # looking-glass, mother-in-law's
    |
    [a-z]+(?:'(?:t|ll|ve|re|d|m|s))\b           # didn't, won't, I'm, we'll, he'd
    |
    [a-z]+'s                                    # Alice's (possessive)
    |
    [a-z]+in'                                   # runnin', nothin' (g-dropping)
    |
    [a-z]+                                      # plain words
    |
    \b[MDCLXVI]+\b                              # Roman numerals
    |
    \d+(?:st|nd|rd|th)                          # Ordinals
    |
    \d{1,3}(?:,\d{3})*(?:\.\d+)?                # Numbers with commas/decimals
    |
    \d+                                         # Plain integers
    """,
    re.VERBOSE | re.IGNORECASE,
)


# =============================================================================
# TOKENIZER IMPLEMENTATION
# =============================================================================


class Tokenizer:
    """
    Text tokenizer for stylometric analysis.

    Handles unicode normalization, text cleaning, and tokenization.
    """

    __slots__ = ("_lowercase", "_min_length", "_strip_numbers")

    def __init__(
        self,
        lowercase: bool = True,
        min_length: int = 1,
        strip_numbers: bool = False,
    ):
        """
        Initialize tokenizer.

        Args:
            lowercase: Normalize tokens to lowercase
            min_length: Minimum token length
            strip_numbers: Exclude numeric tokens
        """
        self._lowercase = lowercase
        self._min_length = min_length
        self._strip_numbers = strip_numbers

    def _iter_tokens(self, text: str) -> Iterator[str]:
        """Yield tokens with filtering applied during iteration."""
        for match in _TOKEN_PATTERN.finditer(text):
            token = match.group(0)

            if len(token) < self._min_length:
                continue

            if self._strip_numbers and token[0].isdigit():
                continue

            if self._lowercase:
                token = token.lower()

            yield token

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into words.

        Args:
            text: Raw input text

        Returns:
            List of tokens
        """
        text = normalize_unicode(text)
        text = clean_text_artifacts(text)
        return list(self._iter_tokens(text))

    def tokenize_iter(self, text: str) -> Iterator[str]:
        """
        Lazily tokenize text (memory-efficient for large documents).

        Args:
            text: Raw input text

        Yields:
            Individual tokens
        """
        text = normalize_unicode(text)
        text = clean_text_artifacts(text)
        yield from self._iter_tokens(text)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def tokenize(text: str, lowercase: bool = True) -> list[str]:
    """Convenience function for simple tokenization."""
    return Tokenizer(lowercase=lowercase).tokenize(text)


def tokenize_iter(text: str, lowercase: bool = True) -> Iterator[str]:
    """Convenience function for lazy tokenization."""
    return Tokenizer(lowercase=lowercase).tokenize_iter(text)
