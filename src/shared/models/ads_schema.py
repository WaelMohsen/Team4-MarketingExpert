from dataclasses import dataclass, field
from typing import Dict, List
import pandas as pd
from src.core.exceptions import SchemaValidationError


@dataclass(frozen=True)
class UnifiedAdsSchema:
    """
    Defines what a valid unified ads analytics table must contain.
    Only validation rules live here.
    """
    # List of columns that MUST exist after normalization
    required_columns: List[str] = field(default_factory=lambda: [
        "date",             # Individual report date
        "platform",         # Source channel identity
        "campaign_type",    # Strategic goal
        "impressions",      # Raw visibility
        "clicks",           # User engagement
        "spend"             # Financial investment
    ])

    # Metadata columns that provide business context for the LLM
    context_columns: List[str] = field(default_factory=lambda: [
        "campaign_name",
        "audience",
        "industry",
        "offering",
        "funnel_stage",
        "country"
    ])

    # Columns that must be numeric for metric calculations
    numeric_columns: List[str] = field(default_factory=lambda: [
        "impressions",
        "clicks",
        "spend",
        "conversions",
        "conversion_value",
        "reach",
        "frequency",
    ])

    # Unified aliases normalized to canonical names.
    unified_aliases: Dict[str, str] = field(default_factory=lambda: {
        "day": "date",
        "report_date": "date",
        "campaign": "campaign_name",
        "campaignname": "campaign_name",
        "campaign title": "campaign_name",
        "campaign type": "campaign_type",
        "platform": "platform",
        "impr.": "impressions",
        "impr": "impressions",
        "click": "clicks",
        "clicks": "clicks",
        "cost": "spend",
        "amount spent": "spend",
        "amount spent (usd)": "spend",
        "results": "conversions",
        "purchases": "conversions",
        "conv value": "conversion_value",
        "conversion value": "conversion_value",
        "revenue": "conversion_value",
    })

    def validate_required(self, df: pd.DataFrame) -> None:
        """Checks for presence of required columns and valid numeric types."""
        missing = [c for c in self.required_columns if c not in df.columns]
        if missing:
            raise SchemaValidationError(f"Missing required unified columns: {missing}")
        
        self.validate_numeric_types(df)
        
    def validate_numeric_types(self, df: pd.DataFrame) -> None:
        """
        Ensures numeric columns contain numeric values.
        Raises SchemaValidationError if non-numeric values are detected.
        """
        errors = []
        for col in self.numeric_columns:
            if col in df.columns:
                # Check for non-numeric values
                if not pd.to_numeric(df[col], errors="coerce").notna().all():
                    # Find which values are problematic (ignoring original NaNs)
                    problematic = df[df[col].notna() & pd.to_numeric(df[col], errors="coerce").isna()][col]
                    if not problematic.empty:
                        errors.append(f"{col} contains invalid values: {problematic.unique()[:3]}")

        if errors:
            raise SchemaValidationError(f"Numeric validation failed: {'; '.join(errors)}")

    def canonicalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizes headers and handles potential duplicate collisions after renaming.
        """
        df = df.copy()
        
        # 1. Clean whitespace and build rename map
        rename_map = {
            col: self.unified_aliases.get(str(col).strip().lower(), str(col).strip()) 
            for col in df.columns
        }
        
        # 2. Apply rename
        df = df.rename(columns=rename_map)
        
        # 3. Handle duplicates (e.g., if 'Cost' and 'spend' both existed)
        if df.columns.duplicated().any():
            # Sum numeric duplicates, take last for categorical
            # To keep it simple and safe for now: just take the last occurrence
            df = df.loc[:, ~df.columns.duplicated(keep="last")]

        return df