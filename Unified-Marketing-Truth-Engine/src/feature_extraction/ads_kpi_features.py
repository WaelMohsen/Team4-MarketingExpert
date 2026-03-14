import numpy as np
import pandas as pd
from typing import Dict, Optional


class AdsKpiFeatures:
    """
    Derived features only (KPIs).
    - Computes KPIs only when inputs exist.
    - By default, does NOT overwrite existing KPI columns.
    """

    # ---------- public API ----------
    @staticmethod
    def compute_kpis(df: pd.DataFrame, *, overwrite: bool = False) -> pd.DataFrame:
        """
        Comput KPI and Adds them as columns to the DataFrame (if inputs exist).
        Each KPI is computed via its own method.
        """
        df = df.copy()

        # ctr
        ctr = AdsKpiFeatures._compute_ctr(df)
        if ctr is not None:
            AdsKpiFeatures._set_if_needed(df, "ctr", ctr, overwrite=overwrite)

        # cpc
        cpc = AdsKpiFeatures._compute_cpc(df)
        if cpc is not None:
            AdsKpiFeatures._set_if_needed(df, "cpc", cpc, overwrite=overwrite)

        # cpm
        cpm = AdsKpiFeatures._compute_cpm(df)
        if cpm is not None:
            AdsKpiFeatures._set_if_needed(df, "cpm", cpm, overwrite=overwrite)

        # cvr
        cvr = AdsKpiFeatures._compute_cvr(df)
        if cvr is not None:
            AdsKpiFeatures._set_if_needed(df, "cvr", cvr, overwrite=overwrite)

        # cpa
        cpa = AdsKpiFeatures._compute_cpa(df)
        if cpa is not None:
            AdsKpiFeatures._set_if_needed(df, "cpa", cpa, overwrite=overwrite)

        # roas
        roas = AdsKpiFeatures._compute_roas(df)
        if roas is not None:
            AdsKpiFeatures._set_if_needed(df, "roas", roas, overwrite=overwrite)

        return df
    
    # ---------- KPI computations (each KPI in its own method) ----------
    def _compute_ctr(df: pd.DataFrame) -> Optional[np.ndarray]:
        if "ctr" in df.columns:
            return None  
        """CTR = clicks / impressions"""
        if {"clicks", "impressions"}.issubset(df.columns):
            return AdsKpiFeatures._safe_div(df["clicks"], df["impressions"])
        return None

    @staticmethod
    def _compute_cpc(df: pd.DataFrame) -> Optional[np.ndarray]:
        if "cpc" in df.columns:
            return None          
        """CPC = spend / clicks"""
        if {"spend", "clicks"}.issubset(df.columns):
            return AdsKpiFeatures._safe_div(df["spend"], df["clicks"])
        return None

    @staticmethod
    def _compute_cpm(df: pd.DataFrame) -> Optional[np.ndarray]:
        if "cpm" in df.columns:
            return None          
        """CPM = (spend / impressions) * 1000"""
        if {"spend", "impressions"}.issubset(df.columns):
            return AdsKpiFeatures._safe_div(df["spend"] * 1000.0, df["impressions"])
        return None

    @staticmethod
    def _compute_cvr(df: pd.DataFrame) -> Optional[np.ndarray]:
        if "cvr" in df.columns:
            return None          
        """CVR = conversions / clicks"""
        if {"conversions", "clicks"}.issubset(df.columns):
            return AdsKpiFeatures._safe_div(df["conversions"], df["clicks"])
        return None

    @staticmethod
    def _compute_cpa(df: pd.DataFrame) -> Optional[np.ndarray]:
        if "cpa" in df.columns:
            return None          
        """CPA = spend / conversions"""
        if {"spend", "conversions"}.issubset(df.columns):
            return AdsKpiFeatures._safe_div(df["spend"], df["conversions"])
        return None

    @staticmethod
    def _compute_roas(df: pd.DataFrame) -> Optional[np.ndarray]:
        if "roas" in df.columns:
            return None          
        """ROAS = conversion_value / spend"""
        if {"conversion_value", "spend"}.issubset(df.columns):
            return AdsKpiFeatures._safe_div(df["conversion_value"], df["spend"])
        return None

    # ---------- helpers ----------
    @staticmethod
    def _safe_div(a: pd.Series, b: pd.Series) -> np.ndarray:
        """Elementwise division with 0/NaN protection (returns np.nan where invalid)."""
        b0 = (b == 0) | b.isna()
        return np.where(b0, np.nan, a / b)
    
    # Helper: write a column only if missing (or overwrite=True)
    @staticmethod
    def _set_if_needed(df: pd.DataFrame, col: str, values: np.ndarray, *, overwrite: bool) -> None:
        """Write KPI column only if missing, unless overwrite=True."""
        if overwrite or col not in df.columns:
            df[col] = values
    