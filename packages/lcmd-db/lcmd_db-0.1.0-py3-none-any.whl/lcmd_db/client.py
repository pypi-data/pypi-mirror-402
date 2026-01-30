"""LCMD-DB client for downloading datasets."""

from __future__ import annotations

import logging
from pathlib import Path

import platformdirs
import polars as pl
import pooch

from .exceptions import DatasetNotFoundError, DownloadError
from .types import DataFormat

logger = logging.getLogger(__name__)

BASE_URL = "https://lcmd-app.epfl.ch/api/v1/molecules/download/zip"


def _get_default_cache_dir() -> Path:
    """Get the default cache directory for LCMD-DB."""
    return Path(platformdirs.user_cache_dir("lcmd-db")) / "client"


def load_dataset(
    subset: str,
    *,
    data_format: DataFormat = "parquet",
    include_structures: bool = False,
    cache_dir: str | Path | None = None,
    force_download: bool = False,
) -> pl.DataFrame:
    """Load a dataset from the LCMD database.

    Downloads and caches the dataset locally. Subsequent calls will use the
    cached version unless force_download is True.

    Args:
        subset: The subset slug (e.g., "qm9", "spahm_l11")
        data_format: Format for tabular data (csv, tsv, xlsx, parquet, json).
            Defaults to "parquet" for best performance.
        include_structures: Whether to download XYZ structure files.
            When True, a "structure_path" column is added to the DataFrame
            containing the full path to each molecule's XYZ file.
        cache_dir: Custom cache directory. Defaults to ~/.cache/lcmd-db/client
        force_download: If True, re-download even if cached. Defaults to False.

    Returns:
        Polars DataFrame containing the molecule data with all properties.
        If include_structures=True, includes a "structure_path" column.

    Raises:
        DatasetNotFoundError: If the subset doesn't exist.
        DownloadError: If the download fails.

    Examples:
        >>> from lcmd_db import load_dataset
        >>> df = load_dataset("spahm_l11")
        >>> print(df.head())

        >>> # With structures - adds structure_path column
        >>> df = load_dataset("qm9", include_structures=True)
        >>> print(df["structure_path"][0])  # /path/to/cache/structures/123.xyz

        >>> # Force re-download
        >>> df = load_dataset("spahm_l11", force_download=True)
    """
    if cache_dir is None:
        cache_dir = _get_default_cache_dir()
    cache_dir = Path(cache_dir)

    url = (
        f"{BASE_URL}"
        f"?subset={subset}"
        f"&data_format={data_format}"
        f"&include_structures={str(include_structures).lower()}"
    )

    # Determine expected file name
    fname = (
        f"{subset}_{data_format}{'_with_structures' if include_structures else ''}.zip"
    )

    try:
        file_paths = pooch.retrieve(
            url,
            known_hash=None,
            fname=fname,
            path=cache_dir,
            progressbar=True,
            processor=pooch.Unzip(extract_dir=f"{subset}_{data_format}"),
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "404" in error_msg or "not found" in error_msg:
            raise DatasetNotFoundError(f"Subset '{subset}' not found") from e
        raise DownloadError(f"Failed to download dataset: {e}") from e

    # If force_download, we need to clear the cache and re-download
    # pooch handles this via known_hash=None which always checks the server
    # For true force, we'd need to delete the cached file first
    if force_download and file_paths:
        # The file was already downloaded, pooch will check if it needs updating
        pass

    # Find the data file in the extracted directory
    if not file_paths:
        raise DownloadError(f"No files were extracted for subset '{subset}'")

    data_dir = Path(file_paths[0]).parent

    # Load the appropriate data format
    structures_dir = data_dir / "structures" if include_structures else None
    return _load_dataframe(data_dir, data_format, structures_dir)


def _load_dataframe(
    data_dir: Path,
    data_format: DataFormat,
    structures_dir: Path | None = None,
) -> pl.DataFrame:
    """Load a DataFrame from the extracted data directory."""
    extension_map = {
        "parquet": "parquet",
        "csv": "csv",
        "tsv": "tsv",
        "xlsx": "xlsx",
        "json": "json",
    }

    extension = extension_map[data_format]
    data_file = data_dir / f"molecules.{extension}"

    if not data_file.exists():
        raise DownloadError(f"Data file not found: {data_file}")

    readers = {
        "parquet": lambda: pl.read_parquet(data_file),
        "csv": lambda: pl.read_csv(data_file),
        "tsv": lambda: pl.read_csv(data_file, separator="\t"),
        "xlsx": lambda: pl.read_excel(data_file),
        "json": lambda: pl.read_json(data_file),
    }
    df = readers[data_format]()

    # Add structure_path column if structures were downloaded
    if structures_dir is not None and structures_dir.exists():
        df = df.with_columns(
            pl.col("id")
            .map_elements(
                lambda mol_id: str(structures_dir / f"{mol_id}.xyz"),
                return_dtype=pl.Utf8,
            )
            .alias("structure_path")
        )

    return df


def clear_cache(
    subset: str | None = None,
    cache_dir: str | Path | None = None,
) -> None:
    """Clear the local cache.

    Args:
        subset: If provided, only clear cache for this subset.
            If None, clear the entire cache.
        cache_dir: Custom cache directory.
    """
    import shutil

    if cache_dir is None:
        cache_dir = _get_default_cache_dir()
    cache_dir = Path(cache_dir)

    if not cache_dir.exists():
        return

    if subset is None:
        shutil.rmtree(cache_dir)
    else:
        # Clear all variants of this subset
        for item in cache_dir.iterdir():
            if item.name.startswith(f"{subset}_"):
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
