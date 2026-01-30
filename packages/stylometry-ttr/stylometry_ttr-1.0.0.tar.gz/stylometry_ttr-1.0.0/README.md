# stylometry-ttr

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Type-Token Ratio (TTR) computation for stylometric analysis.

## What is TTR?

TTR measures vocabulary richness: the ratio of unique words (types) to total words (tokens). This package computes multiple TTR variants to account for text length bias:

| Metric | Formula | Description |
|--------|---------|-------------|
| **Raw TTR** | unique / total | Simple ratio, biased toward short texts |
| **Root TTR** | unique / sqrt(total) | Guiraud's index, normalizes for length |
| **Log TTR** | log(unique) / log(total) | Herdan's C, normalizes for length |
| **STTR** | mean(TTR per chunk) | Standardized TTR across fixed-size chunks |

## Installation

```bash
pip install stylometry-ttr
```

## Usage

```python
from stylometry_ttr import compute_ttr

text = open("novel.txt").read()
result = compute_ttr(text, text_id="novel-001")

print(result)
```

Output:
```
+----------------------------------------------------------+
| TTR Report: novel-001                                    |
+----------------------------+-----------------------------+
| Metric                     |                       Value |
+----------------------------+-----------------------------+
| Total Words                |                      59,261 |
| Unique Words               |                       5,747 |
| TTR                        |                    0.096978 |
| Root TTR                   |                     23.6079 |
| Log TTR                    |                    0.787686 |
| STTR                       |                    0.414712 |
+----------------------------+-----------------------------+
```

For JSON output:
```python
print(result.to_json())
```

## Example: The Hound of the Baskervilles

Results from analyzing Arthur Conan Doyle's novel:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Total Words | 59,261 | Full novel length |
| Unique Words | 5,747 | Vocabulary size |
| TTR | 0.097 | 9.7% unique words (typical for novels: 0.05-0.15) |
| Root TTR | 23.6 | Length-normalized richness |
| Log TTR | 0.788 | Near 1.0 indicates rich vocabulary |
| STTR | 0.415 | ~41.5% unique words per 1000-word chunk |
| Delta Std | 0.030 | Low variability = consistent vocabulary throughout |

## Documentation

See [docs/API.md](docs/API.md) for full API reference including:
- All import styles and functions
- Configuration options
- Output formats (table, JSON, dict)
- Model field descriptions

## Development

```bash
make all        # Install, lint, test
make test       # Run tests only
make lint       # Check code style
```
