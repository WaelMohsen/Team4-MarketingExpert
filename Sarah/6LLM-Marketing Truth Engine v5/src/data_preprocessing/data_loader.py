from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd

Source = Union[pd.DataFrame, str, Path]


@dataclass
class AdsDataLoader:
    """
    Loads ads analytics data from different sources into a pandas DataFrame.

    Responsibilities:
    - Accept pd.DataFrame (pass-through copy)
    - Accept file paths: .csv, .xlsx/.xls, .json, .parquet
    - Optional light cleanup: strip column names, drop fully-empty columns
    """

    strip_column_whitespace: bool = True
    drop_all_null_columns: bool = True

    def load( self, source: Source, *, read_kwargs: Optional[Dict[str, Any]] = None,) -> pd.DataFrame:
        """
        Loads the source into a DataFrame.

        Args:
            source: DataFrame or path to file.
            read_kwargs: optional kwargs passed into pandas read_* functions.

        Returns:
            pd.DataFrame
        """
        read_kwargs = read_kwargs or {}

        df = self._read(source, read_kwargs=read_kwargs)
        df = self._post_process(df)
        return df

    # ----------------------------
    # Internals
    # ----------------------------
    def _read(self, source: Source, *, read_kwargs: Dict[str, Any]) -> pd.DataFrame:
        """Read from DataFrame or supported file formats."""
        if isinstance(source, pd.DataFrame):
            return source.copy()

        path = Path(source)  # supports str or Path
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()

        if suffix == ".csv":
            return pd.read_csv(path, **read_kwargs)

        if suffix in (".xlsx", ".xls"):
            return pd.read_excel(path, **read_kwargs)

        if suffix == ".json":
            # If your JSON is lines-delimited, pass read_kwargs={"lines": True}
            return pd.read_json(path, **read_kwargs)

        if suffix == ".parquet":
            return pd.read_parquet(path, **read_kwargs)

        raise ValueError(
            f"Unsupported file type '{suffix}'. Supported: .csv, .xlsx/.xls, .json, .parquet"
        )

    def _post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Light cleanup that is safe for all platforms."""
        df = df.copy()

        if self.strip_column_whitespace:
            # Strip whitespace and normalize weird spacing in headers
            df.columns = [str(c).strip() for c in df.columns]

        if self.drop_all_null_columns:
            df = df.dropna(axis=1, how="all")

        return df