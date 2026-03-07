
import pandas as pd
 

from src.schema import (
    REQUIRED_COLUMNS,
    COLUMN_MAP,
    COLUMN_TYPES,
    PLATFORM_NAME_MAP,
)

class DataLoader:
     """
       Load and validate the ads performance CSV.

       Steps:
      1. Read CSV
      2. Rename columns to internal schema
      3. Validate required columns are present
      4. Normalise platform names
      5. Cast column types
      6. Handle missing / invalid values
      7. Filter out zero-spend rows
      8. Print validation report
      9. Return clean DataFrame
     """
    
     def __init__(self, filepath: str):
        self.filepath = filepath
        self._skipped_raws=0
     # ── Public interface ───────────────────────────────────────────────────────

     def load(self) -> pd.DataFrame:
        """Load and return a clean, normalised DataFrame."""
        raw_df = self._read_csv()
        df     = self._rename_columns(raw_df)
        self._validate_columns(df)
        df     = self._normalise_platforms(df)
        df     = self._cast_types(df)
        df     = self._handle_missing(df)
        self._print_validation_report(df)
        return df.reset_index(drop=True)

     # ── Step 1: Read CSV ───────────────────────────────────────────────────────

     def _read_csv(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.filepath)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Dataset not found at '{self.filepath}'.\n"
                "Place your CSV at data/ads_performance.csv or pass the correct path."
            )
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {e}")

        if df.empty:
            raise ValueError("The CSV file is empty.")

        return df

        # ── Step 2: Rename columns ─────────────────────────────────────────────────

     def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {col: COLUMN_MAP[col] for col in df.columns if col in COLUMN_MAP}
        return df.rename(columns=rename_map)

     # ── Step 3: Validate required columns ─────────────────────────────────────

     def _validate_columns(self, df: pd.DataFrame):
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(
                f"Missing required columns in '{self.filepath}': {missing}\n"
                f"Found columns: {list(df.columns)}\n"
                "Check schema.py → COLUMN_MAP to add an alias for your CSV's field names."
            )
     
    # ── Step 4: Normalise platform names ──────────────────────────────────────
     """ take every platform name, trim its whitespace, lowercase it,
     swap it for the official name if we recognise it, and leave it alone if we don't.
     The result is a column where "facebook", "FB", and "Facebook" all become "Meta",
     ready for consistent grouping and comparison downstream."""
     def _normalise_platforms(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["platform"] = (
            df["platform"]
            .str.strip()
            .apply(
                lambda p: PLATFORM_NAME_MAP.get(p.lower(), p)
                if isinstance(p, str) else p
            )
        )
        return df

    # ── Step 5: Cast column types ──────────────────────────────────────────────

     def _cast_types(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col, dtype in COLUMN_TYPES.items():
            if col not in df.columns:
                continue
            if dtype == int:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            elif dtype == float:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(float)
        return df
    
     # ── Step 6: Handle missing values ─────────────────────────────────────────

     def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        before = len(df)
        df = df.dropna(subset=["campaign_id", "platform", "spend", "impressions", "clicks", "conversions", "revenue"])
        self._skipped_raws += before - len(df)
        return df
   
   
    # ── Step 7: Validation report ──────────────────────────────────────────────

     def _print_validation_report(self, df: pd.DataFrame):
        platforms     = sorted(df["platform"].unique().tolist())
        date_min      = df["date"].min()
        date_max      = df["date"].max()
        total_spend   = df["spend"].sum()
        total_revenue = df["revenue"].sum()

        print()
        print("=" * 52)
        print("  DATA LOAD — VALIDATION REPORT")
        print("=" * 52)
        print(f"  ✅  Rows loaded          : {len(df):,}")
        print(f"  ✅  Platforms detected   : {', '.join(platforms)}")
        print(f"  ✅  Date range           : {date_min} → {date_max}")


        if self._skipped_raws:
            print(f"  ⚠   Rows skipped (no ID/platform) : {self._skipped_raws}")
         

        print("=" * 52)
        print()
