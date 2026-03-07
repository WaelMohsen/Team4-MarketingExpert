
"""
transform.py — Converts MetricsCalculator output into structured JSON.

Usage:
    results     = MetricsCalculator(df).calculate()
    transformer = DataTransformer(results)
    transformer.to_json("output/metrics.json")

    # Or get the dict directly without writing to file:
    data = transformer.transform()
"""

import json
import os
from datetime import datetime


class DataTransformer:
    """
    Takes the results dict produced by MetricsCalculator and converts it
    into a clean, serialisable JSON structure.

    Handles:
        - NaN / None / Infinity values (converts to null in JSON)
        - Pandas int64 / float64 types (converts to native Python types)
        - Automatic totals calculation across all platforms
        - Optional file output with a single method call

    Input (results dict from MetricsCalculator.calculate()):
        {
            "platform_df": DataFrame   ← per-platform aggregated metrics
        }

    Output JSON shape:
        {
        
            "platform_summary": [ { per-platform record }, ... ],
            "totals": {
                "total_spend":       float,
                "total_revenue":     float,
                "total_conversions": int,
                "total_clicks":      int,
                "total_impressions": int,
                "overall_roas":      float
            }
        }
    """

    def __init__(self, results: dict):
        self._platform_df = results.get("platform_df")

        if self._platform_df is None:
            raise ValueError(
                "Results dict must contain 'platform_df'. "
                "Make sure you are passing the output of MetricsCalculator.calculate()."
            )

    # ── Public interface ───────────────────────────────────────────────────────

    def transform(self) -> dict:
        """
        Build and return the JSON-ready output dict.
        Does not write to disk — use to_json() for that.
        """
        output = {
            "platform_summary": self._build_platform_summary(),
            "totals":           self._build_totals(),
        }
        return self._clean(output)

    def to_json(self, filepath: str) -> dict:
        """
        Build the output, write it to filepath, and return the dict.

        Creates any missing parent directories automatically.
        """
        data = self.transform()

        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"  ✅  Metrics JSON written → {filepath}")
        return data

    # ── Builders ───────────────────────────────────────────────────────────────

    def _build_platform_summary(self) -> list:
        """Convert each platform row into a plain dict."""
        records = []
        for _, row in self._platform_df.iterrows():
            records.append({
                "platform":         row["platform"],
                "total_spend":      self._to_float(row["total_spend"]),
                "total_revenue":    self._to_float(row["total_revenue"]),
                "total_impressions":self._to_int(row["total_impressions"]),
                "total_clicks":     self._to_int(row["total_clicks"]),
                "total_conversions":self._to_int(row["total_conversions"]),
                "platform_roas":    self._to_float(row["platform_roas"]),
                "platform_cac":     self._to_float(row.get("platform_cac")),
                "platform_cvr":     self._to_float(row.get("platform_cvr")),
                "platform_ctr":     self._to_float(row.get("platform_ctr")),
                "spend_share_pct":  self._to_float(row["spend_share"]),
            })
        return records

    def _build_totals(self) -> dict:
        """Aggregate across all platforms into a single totals block."""
        df = self._platform_df

        total_spend   = float(df["total_spend"].sum())
        total_revenue = float(df["total_revenue"].sum())

        return {
            "total_spend":        round(total_spend, 2),
            "total_revenue":      round(total_revenue, 2),
            "total_conversions":  int(df["total_conversions"].sum()),
            "total_clicks":       int(df["total_clicks"].sum()),
            "total_impressions":  int(df["total_impressions"].sum()),
            "overall_roas":       round(total_revenue / total_spend, 2)
                                  if total_spend > 0 else None,
        }

    # ── Type converters ────────────────────────────────────────────────────────

    @staticmethod
    def _to_float(value) -> float | None:
        """Convert a value to a native Python float, or None if not valid."""
        try:
            v = float(value)
            # Treat NaN and Infinity as null in JSON
            if v != v or v in (float("inf"), float("-inf")):
                return None
            return round(v, 2)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value) -> int | None:
        """Convert a value to a native Python int, or None if not valid."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    # ── NaN / type cleaner (recursive safety net) ─────────────────────────────

    def _clean(self, obj):
        """
        Recursively walk the output and replace any remaining
        NaN / Infinity / Pandas types with JSON-safe equivalents.
        """
        if isinstance(obj, dict):
            return {k: self._clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._clean(v) for v in obj]
        if isinstance(obj, float):
            if obj != obj or obj in (float("inf"), float("-inf")):
                return None
            return obj
        # Convert numpy / pandas numeric types to native Python
        if hasattr(obj, "item"):
            return obj.item()
        return obj
