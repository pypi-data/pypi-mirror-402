"""
Type-Token Ratio (TTR) metric implementations.

TTR measures vocabulary richness: the ratio of unique words (types)
to total words (tokens). This module provides four variants:

1. Raw TTR: unique / total (biased toward short texts)
2. Root TTR: unique / sqrt(total) (normalizes for length)
3. Log TTR: log(unique) / log(total) (normalizes for length)
4. STTR: Mean TTR across fixed-size chunks (standardized)
"""

import math
import statistics
from dataclasses import dataclass
from typing import Optional

from stylometry_ttr.models import TTRResult, TTRAggregate


@dataclass
class TTRConfig:
    """Configuration for TTR computation."""

    sttr_chunk_size: int = 1000  # Words per chunk for STTR
    min_words_for_sttr: int = 2000  # Minimum words to compute STTR


class TTRCalculator:
    """
    Calculator for Type-Token Ratio metrics.

    Computes multiple TTR variants to account for text length bias.
    """

    def __init__(self, config: Optional[TTRConfig] = None):
        """
        Initialize calculator.

        Args:
            config: Configuration options (uses defaults if not provided)
        """
        self._config = config or TTRConfig()

    def compute(
        self,
        tokens: list[str],
        text_id: str,
        title: str = "",
        author: str = "",
    ) -> TTRResult:
        """
        Compute all TTR variants for a token list.

        Args:
            tokens: List of word tokens
            text_id: Unique identifier for the text
            title: Title of the text (optional)
            author: Author identifier (optional)

        Returns:
            TTRResult with all computed metrics
        """
        total_words = len(tokens)

        if total_words == 0:
            return TTRResult(
                text_id=text_id,
                title=title,
                author=author,
                total_words=0,
                unique_words=0,
                ttr=0.0,
                root_ttr=0.0,
                log_ttr=0.0,
                sttr=None,
                sttr_std=None,
                chunk_count=None,
                delta_mean=None,
                delta_std=None,
                delta_min=None,
                delta_max=None,
            )

        # Count unique words
        unique_words = len(set(tokens))

        # Raw TTR
        ttr = unique_words / total_words

        # Root TTR (Guiraud's index)
        root_ttr = unique_words / math.sqrt(total_words)

        # Log TTR (Herdan's C)
        log_ttr = math.log(unique_words) / math.log(total_words) if total_words > 1 else 0.0

        # Standardized TTR and deltas (computed on fixed-size chunks)
        sttr, sttr_std, chunk_count, delta_mean, delta_std, delta_min, delta_max = (
            self._compute_sttr(tokens)
        )

        return TTRResult(
            text_id=text_id,
            title=title,
            author=author,
            total_words=total_words,
            unique_words=unique_words,
            ttr=round(ttr, 6),
            root_ttr=round(root_ttr, 4),
            log_ttr=round(log_ttr, 6),
            sttr=round(sttr, 6) if sttr is not None else None,
            sttr_std=round(sttr_std, 6) if sttr_std is not None else None,
            chunk_count=chunk_count,
            delta_mean=round(delta_mean, 6) if delta_mean is not None else None,
            delta_std=round(delta_std, 6) if delta_std is not None else None,
            delta_min=round(delta_min, 6) if delta_min is not None else None,
            delta_max=round(delta_max, 6) if delta_max is not None else None,
        )

    def _compute_sttr(
        self, tokens: list[str]
    ) -> tuple[
        Optional[float],
        Optional[float],
        Optional[int],
        Optional[float],
        Optional[float],
        Optional[float],
        Optional[float],
    ]:
        """
        Compute Standardized TTR and delta metrics using fixed-size chunks.

        STTR averages the TTR across non-overlapping chunks of text,
        which normalizes for document length.

        Delta metrics capture chunk-to-chunk variability: TTR(n) - TTR(n-1)

        Args:
            tokens: List of tokens

        Returns:
            Tuple of (mean_sttr, std_sttr, chunk_count, delta_mean, delta_std, delta_min, delta_max)
        """
        total_words = len(tokens)
        chunk_size = self._config.sttr_chunk_size

        # Need minimum words
        if total_words < self._config.min_words_for_sttr:
            return None, None, None, None, None, None, None

        # Compute TTR for each chunk
        chunk_ttrs: list[float] = []

        for i in range(0, total_words - chunk_size + 1, chunk_size):
            chunk = tokens[i : i + chunk_size]
            chunk_unique = len(set(chunk))
            chunk_ttr = chunk_unique / chunk_size
            chunk_ttrs.append(chunk_ttr)

        if not chunk_ttrs:
            return None, None, None, None, None, None, None

        mean_sttr = statistics.mean(chunk_ttrs)
        std_sttr = statistics.stdev(chunk_ttrs) if len(chunk_ttrs) > 1 else 0.0

        # Compute deltas: TTR(n) - TTR(n-1)
        if len(chunk_ttrs) < 2:
            return mean_sttr, std_sttr, len(chunk_ttrs), None, None, None, None

        deltas = [chunk_ttrs[i] - chunk_ttrs[i - 1] for i in range(1, len(chunk_ttrs))]
        delta_mean = statistics.mean(deltas)
        delta_std = statistics.stdev(deltas) if len(deltas) > 1 else 0.0
        delta_min = min(deltas)
        delta_max = max(deltas)

        return mean_sttr, std_sttr, len(chunk_ttrs), delta_mean, delta_std, delta_min, delta_max


class TTRAggregator:
    """Aggregates per-text TTR results into group-level statistics."""

    def aggregate(self, results: list[TTRResult], group_id: str) -> TTRAggregate:
        """
        Compute aggregate statistics from multiple TTR results.

        Args:
            results: List of per-text TTR results
            group_id: Identifier for the group (e.g., author name)

        Returns:
            TTRAggregate with aggregate statistics
        """
        if not results:
            raise ValueError("Cannot aggregate empty results list")

        ttrs = [r.ttr for r in results]
        root_ttrs = [r.root_ttr for r in results]
        log_ttrs = [r.log_ttr for r in results]
        sttrs = [r.sttr for r in results if r.sttr is not None]
        delta_stds = [r.delta_std for r in results if r.delta_std is not None]

        return TTRAggregate(
            group_id=group_id,
            text_count=len(results),
            total_words=sum(r.total_words for r in results),
            ttr_mean=round(statistics.mean(ttrs), 6),
            ttr_std=round(statistics.stdev(ttrs), 6) if len(ttrs) > 1 else 0.0,
            ttr_min=round(min(ttrs), 6),
            ttr_max=round(max(ttrs), 6),
            ttr_median=round(statistics.median(ttrs), 6),
            root_ttr_mean=round(statistics.mean(root_ttrs), 4),
            root_ttr_std=round(statistics.stdev(root_ttrs), 4) if len(root_ttrs) > 1 else 0.0,
            log_ttr_mean=round(statistics.mean(log_ttrs), 6),
            log_ttr_std=round(statistics.stdev(log_ttrs), 6) if len(log_ttrs) > 1 else 0.0,
            sttr_mean=round(statistics.mean(sttrs), 6) if sttrs else None,
            sttr_std=round(statistics.stdev(sttrs), 6) if len(sttrs) > 1 else None,
            delta_std_mean=round(statistics.mean(delta_stds), 6) if delta_stds else None,
        )
