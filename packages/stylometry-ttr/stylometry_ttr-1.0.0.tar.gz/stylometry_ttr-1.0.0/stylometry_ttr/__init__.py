"""
Type-Token Ratio (TTR) computation for stylometric analysis.

This package provides tools for computing vocabulary richness metrics
using various TTR variants.

Usage:
    # Simple (recommended)
    from stylometry_ttr import compute_ttr
    result = compute_ttr(text, text_id="doc1")

    # Namespace style
    import stylometry_ttr as ttr
    result = ttr.compute(text, text_id="doc1")
    tokens = ttr.tokenize(text)
"""

__version__ = "1.0.0"

from typing import Optional

from stylometry_ttr.models import TTRResult, TTRAggregate
from stylometry_ttr.ttr import TTRCalculator, TTRConfig, TTRAggregator
from stylometry_ttr.tokenizer import Tokenizer, tokenize, tokenize_iter


def compute_ttr(
    text: str,
    text_id: str,
    title: str = "",
    author: str = "",
    config: Optional[TTRConfig] = None,
) -> TTRResult:
    """
    Compute TTR metrics from raw text.

    This is the recommended entry point for most users.

    Args:
        text: Raw input text
        text_id: Unique identifier for the text
        title: Title of the text (optional)
        author: Author identifier (optional)
        config: TTR configuration (optional, uses defaults if not provided)

    Returns:
        TTRResult with all computed metrics
    """
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(text)
    calculator = TTRCalculator(config=config)
    return calculator.compute(tokens, text_id=text_id, title=title, author=author)


# Alias for namespace-style usage: ttr.compute()
compute = compute_ttr


__all__ = [
    "__version__",
    # Primary API
    "compute_ttr",
    "compute",
    "tokenize",
    # Models
    "TTRResult",
    "TTRAggregate",
    # Power user classes
    "TTRCalculator",
    "TTRConfig",
    "TTRAggregator",
    "Tokenizer",
    "tokenize_iter",
]
