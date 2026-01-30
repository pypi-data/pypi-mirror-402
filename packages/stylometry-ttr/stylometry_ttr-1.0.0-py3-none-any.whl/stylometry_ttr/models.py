"""
Pydantic models for TTR computation.

These models define the data structures for TTR results and aggregates.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TTRResult(BaseModel):
    """Type-Token Ratio results for a single text."""

    model_config = ConfigDict(frozen=True)

    text_id: str = Field(..., description="Unique identifier for the text")
    title: str = Field(default="", description="Title of the text")
    author: str = Field(default="", description="Author identifier")
    total_words: int = Field(..., ge=0, description="Total token count")
    unique_words: int = Field(..., ge=0, description="Unique token count (types)")
    ttr: float = Field(..., ge=0.0, le=1.0, description="Raw TTR: unique/total")
    root_ttr: float = Field(..., ge=0.0, description="Root TTR: unique/sqrt(total)")
    log_ttr: float = Field(..., ge=0.0, description="Log TTR: log(unique)/log(total)")
    sttr: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Standardized TTR (1000-word chunks)"
    )
    sttr_std: Optional[float] = Field(None, ge=0.0, description="STTR standard deviation")
    chunk_count: Optional[int] = Field(None, ge=0, description="Number of chunks for STTR")

    # Delta metrics: TTR(n) - TTR(n-1) between consecutive chunks
    delta_mean: Optional[float] = Field(None, description="Mean of chunk-to-chunk TTR deltas")
    delta_std: Optional[float] = Field(None, ge=0.0, description="Std dev of TTR deltas (volatility)")
    delta_min: Optional[float] = Field(None, description="Largest negative swing")
    delta_max: Optional[float] = Field(None, description="Largest positive swing")

    def to_json(self, indent: int = 2, exclude_none: bool = True) -> str:
        """Return JSON string representation."""
        return self.model_dump_json(indent=indent, exclude_none=exclude_none)

    def to_table(self) -> str:
        """Return ASCII table representation."""
        title = self.title or self.text_id
        lines = [
            f"+{'-' * 58}+",
            f"| {'TTR Report: ' + title:<56} |",
            f"+{'-' * 28}+{'-' * 29}+",
            f"| {'Metric':<26} | {'Value':>27} |",
            f"+{'-' * 28}+{'-' * 29}+",
            f"| {'Total Words':<26} | {self.total_words:>27,} |",
            f"| {'Unique Words':<26} | {self.unique_words:>27,} |",
            f"| {'TTR':<26} | {self.ttr:>27.6f} |",
            f"| {'Root TTR':<26} | {self.root_ttr:>27.4f} |",
            f"| {'Log TTR':<26} | {self.log_ttr:>27.6f} |",
        ]
        if self.sttr is not None:
            lines.append(f"| {'STTR':<26} | {self.sttr:>27.6f} |")
        if self.sttr_std is not None:
            lines.append(f"| {'STTR Std':<26} | {self.sttr_std:>27.6f} |")
        if self.chunk_count is not None:
            lines.append(f"| {'Chunk Count':<26} | {self.chunk_count:>27} |")
        if self.delta_mean is not None:
            lines.append(f"| {'Delta Mean':<26} | {self.delta_mean:>27.6f} |")
        if self.delta_std is not None:
            lines.append(f"| {'Delta Std':<26} | {self.delta_std:>27.6f} |")
        if self.delta_min is not None:
            lines.append(f"| {'Delta Min':<26} | {self.delta_min:>27.6f} |")
        if self.delta_max is not None:
            lines.append(f"| {'Delta Max':<26} | {self.delta_max:>27.6f} |")
        lines.append(f"+{'-' * 28}+{'-' * 29}+")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Return ASCII table representation."""
        return self.to_table()


class TTRAggregate(BaseModel):
    """Aggregated TTR statistics for a collection of texts."""

    model_config = ConfigDict(frozen=True)

    group_id: str = Field(..., description="Identifier for the group (e.g., author name)")
    text_count: int = Field(..., ge=0)
    total_words: int = Field(..., ge=0, description="Sum of words across all texts")

    ttr_mean: float
    ttr_std: float
    ttr_min: float
    ttr_max: float
    ttr_median: float

    root_ttr_mean: float
    root_ttr_std: float

    log_ttr_mean: float
    log_ttr_std: float

    sttr_mean: Optional[float] = None
    sttr_std: Optional[float] = None

    delta_std_mean: Optional[float] = None

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self, indent: int = 2, exclude_none: bool = True) -> str:
        """Return JSON string representation."""
        return self.model_dump_json(indent=indent, exclude_none=exclude_none)

    def to_table(self) -> str:
        """Return ASCII table representation."""
        lines = [
            f"+{'-' * 58}+",
            f"| {'TTR Aggregate: ' + self.group_id:<56} |",
            f"+{'-' * 28}+{'-' * 29}+",
            f"| {'Metric':<26} | {'Value':>27} |",
            f"+{'-' * 28}+{'-' * 29}+",
            f"| {'Text Count':<26} | {self.text_count:>27} |",
            f"| {'Total Words':<26} | {self.total_words:>27,} |",
            f"| {'TTR Mean':<26} | {self.ttr_mean:>27.6f} |",
            f"| {'TTR Std':<26} | {self.ttr_std:>27.6f} |",
            f"| {'TTR Min':<26} | {self.ttr_min:>27.6f} |",
            f"| {'TTR Max':<26} | {self.ttr_max:>27.6f} |",
            f"| {'TTR Median':<26} | {self.ttr_median:>27.6f} |",
            f"| {'Root TTR Mean':<26} | {self.root_ttr_mean:>27.4f} |",
            f"| {'Root TTR Std':<26} | {self.root_ttr_std:>27.4f} |",
            f"| {'Log TTR Mean':<26} | {self.log_ttr_mean:>27.6f} |",
            f"| {'Log TTR Std':<26} | {self.log_ttr_std:>27.6f} |",
        ]
        if self.sttr_mean is not None:
            lines.append(f"| {'STTR Mean':<26} | {self.sttr_mean:>27.6f} |")
        if self.sttr_std is not None:
            lines.append(f"| {'STTR Std':<26} | {self.sttr_std:>27.6f} |")
        if self.delta_std_mean is not None:
            lines.append(f"| {'Delta Std Mean':<26} | {self.delta_std_mean:>27.6f} |")
        lines.append(f"+{'-' * 28}+{'-' * 29}+")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Return ASCII table representation."""
        return self.to_table()
