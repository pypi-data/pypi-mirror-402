# alpha101

**alpha101** is a Python implementation of the "101 Formulaic Alphas" by WorldQuant.

Binary factors that take values in $\{0, 1\}$ or $\{−1, 1\}$ (e.g., Alpha#21) are difficult to analyze using standard asset pricing methods like portfolio sorts or Fama-MacBeth regressions, thus currently **not implemented**.

**Reference Paper**: Kakushadze, Z. (2016), 101 Formulaic Alphas. Wilmott, 2016: 72-81. <https://doi.org/10.1002/wilm.10525>

---

## Installation

Install the package directly from PyPI:

```bash
pip install alpha101
```

---

## Data Preparation

To use this library, your input data must be a **pandas DataFrame** with a specific structure.

### Required Format

* **Index**: A MultiIndex consisting of `["symbol", "date"]`.
* **Columns**: The following columns are required:
* `open`, `high`, `low`, `close`, `volume`, `market_value`, `return`, `vwap`, `industry`.

### Data Structure Example

```text
                      open     high      low    close    volume  market_value    return        vwap industry
symbol date                                                                                                 
000001 2012-01-05  737.295  756.263  735.836  748.481  24408005  7.884836e+10  0.015172  748.962257   440101
       2012-01-06  746.536  754.317  736.809  746.536  13315115  7.864343e+10 -0.002599  745.647035   440101
       2012-01-09  747.022  768.908  741.672  767.449  22113866  8.084647e+10  0.028013  760.810964   440101
       2012-01-31  813.165  817.056  802.465  809.274  17326547  8.525255e+10 -0.004189  809.167648   440101
       2012-02-01  806.356  817.056  799.061  800.034  18515899  8.427911e+10 -0.011418  808.197719   440101
...                    ...      ...      ...      ...       ...           ...       ...         ...      ...
689009 2025-12-25   60.735   61.324   60.487   61.034   3726782  4.255022e+10  0.000836   60.974976   280401
       2025-12-26   60.962   61.014   58.678   58.761   9845504  4.096548e+10 -0.037242   59.541033   280401
       2025-12-29   58.668   59.247   57.376   57.459   8234821  4.005786e+10 -0.022158   58.141869   280401
       2025-12-30   57.459   58.224   57.098   57.655   4441402  4.019473e+10  0.003411   57.702708   280401
       2025-12-31   57.655   58.224   57.366   57.438   4451676  4.004345e+10 -0.003764   57.788363   280401

[10578521 rows x 9 columns]
```

---

## Usage

### 1. Basic Usage

Initialize the `Alphas` class with your DataFrame and call the desired alpha method.

```python
import pandas as pd
from alpha101 import Alphas

# Load your data
data = pd.read_feather("path/to/your/data.feather").set_index(["symbol", "date"])
data.sort_index(inplace=True)

# Initialize and compute a specific alpha
alphas = Alphas(data)
alpha_42 = alphas.alpha_42()

print(alpha_42.head())
```

### 2. Batch Calculation

You can iterate through all implemented alphas using Python's `getattr`:

```python
for i in range(1, 102):
    try:
        method_name = f"alpha_{i}"
        alpha_series = getattr(alphas, method_name)()
        # Save or process your alpha_series here
    except (NotImplementedError, AttributeError):
        print(f"Alpha_{i} is not implemented or available.")
        continue
```

---

## Output

Each method returns a **pandas Series** with the same MultiIndex (`symbol`, `date`) as the input, containing the calculated signal values.

```text
symbol  date      
000001  2012-01-05    0.599195
        2012-01-06    0.182127
        2012-01-09    0.022663
        2012-01-31    0.535393
        2012-02-01    1.004452
                        ...   
689009  2025-12-25    0.933398
        2025-12-26    1.493355
        2025-12-29    1.439205
        2025-12-30    0.761360
        2025-12-31    1.378834
Length: 10578521, dtype: float64
```
