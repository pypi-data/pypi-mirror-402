# LCMD-DB

Python client for the [LCMD molecular database](https://lcmd-app.epfl.ch).

## Installation

```bash
uv add lcmd-db
# or
pip install lcmd-db
```

## Usage

```python
from lcmd_db import load_dataset

# Load a dataset
df = load_dataset("spahm_l11")

# Load with XYZ structures (adds structure_path column)
df = load_dataset("spahm_l11", include_structures=True)
print(df["structure_path"][0])

# Force re-download (bypass cache)
df = load_dataset("spahm_l11", force_download=True)

# Clear cache
from lcmd_db import clear_cache
clear_cache()  # Clear all
clear_cache("spahm_l11")  # Clear specific dataset
```

## Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `subset` | Dataset slug (e.g., "spahm_l11", "qm9") | required |
| `data_format` | Output format: "parquet", "csv", "json", "xlsx", "tsv" | "parquet" |
| `include_structures` | Download XYZ files and add `structure_path` column | False |
| `cache_dir` | Custom cache directory | OS-dependent |
| `force_download` | Bypass cache and re-download | False |

## Available Datasets

Browse datasets at [lcmd-app.epfl.ch](https://lcmd-app.epfl.ch).
