# smartcalc-utils

Smart calculation utilities for finance and statistical analysis.

## Features

- **Finance Tools**: EMI calculations, compound interest, and more
- **Data Statistics**: Statistical analysis and data processing utilities

## Installation

```bash
pip install smartcalc-utils
```

## Usage

### Finance Tools

```python
from smartcalc_utils.finance_tools import calculate_emi

emi = calculate_emi(principal=100000, rate=5, months=12)
print(emi)
```

### Data Statistics

```python
from smartcalc_utils.data_stats import calculate_stats

stats = calculate_stats([1, 2, 3, 4, 5])
print(stats)
```

## License

MIT License - See LICENSE file for details

## Author

Your Name - your.email@example.com
