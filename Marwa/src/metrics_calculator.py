"""
 metrics_calculator.py — Computes all business metrics for the Truth Engine.

 Usage:
    calculator = MetricsCalculator(df)
    results = calculator.calculate()
  
"""
import pandas as pd


class MetricsCalculator:
     """
     Computes campaign-level, platform-level, and global benchmark metrics
     from the clean DataFrame produced by DataLoader.

     Metrics calculated:
        
        Platform level : aggregated ROAS, CAC, CVR, CTR, Spend Share
       
     """

     def __init__(self, df: pd.DataFrame):
        self._df = df
        self._total_spend = df["spend"].sum()

    # ── Public interface ───────────────────────────────────────────────────────

     def calculate(self) -> dict:
        """
        Run all metric calculations.

        Returns:
            {
               
                "platform_df"  : DataFrame with per-platform aggregations,
                
            }
        """
        
        platform_df = self._calculate_platform_metrics()
        

        self._print_summary( platform_df)

        return {
            
            "platform_df": platform_df,
           
        }

    # ── platform_-level metrics ─────────────────────────────────────────────────


     def _calculate_platform_metrics(self) -> pd.DataFrame:
        """Aggregate all rows per platform and compute platform-level metrics."""
        agg = (
            self._df.groupby("platform")
            .agg(
                total_spend       =("spend",       "sum"),
                total_revenue     =("revenue",     "sum"),
                total_impressions =("impressions", "sum"),
                total_clicks      =("clicks",      "sum"),
                total_conversions =("conversions", "sum"),
            )
            .reset_index()
        )

        agg["platform_roas"] = (agg["total_revenue"] / agg["total_spend"]).round(2)

        agg["platform_cac"] = agg.apply(
            lambda r: round(r["total_spend"] / r["total_conversions"], 2)
            if r["total_conversions"] > 0 else None,
            axis=1,
        )

        agg["platform_cvr"] = agg.apply(
            lambda r: round(r["total_conversions"] / r["total_clicks"] * 100, 2)
            if r["total_clicks"] > 0 else None,
            axis=1,
        )

        agg["platform_ctr"] = agg.apply(
            lambda r: round(r["total_clicks"] / r["total_impressions"] * 100, 2)
            if r["total_impressions"] > 0 else None,
            axis=1,
        )

        agg["spend_share"] = (agg["total_spend"] / self._total_spend * 100).round(2)

        return agg.sort_values("platform_roas", ascending=False).reset_index(drop=True)



    # ── Summary report ─────────────────────────────────────────────────────────

     def _print_summary(self, platform_df):
        print()
        print("=" * 52)
        print("  METRICS CALCULATOR — SUMMARY")
        print("=" * 52)

        print("\n  📊  PLATFORM BREAKDOWN\n")
        print(f"  {'Platform':<10} {'ROAS':>6} {'CAC':>8} {'CVR':>7} {'Spend Share':>12}")
        print(f"  {'-'*10} {'-'*6} {'-'*8} {'-'*7} {'-'*12}")
        for _, row in platform_df.iterrows():
             cac_str = f"${row['platform_cac']:>6.2f}" if row["platform_cac"] else "   N/A"
             cvr_str = f"{row['platform_cvr']:>5.2f}%" if row["platform_cvr"] else "   N/A"
             print(
                f"  {row['platform']:<10} "
                f"{row['platform_roas']:>6.2f} "
                f"{cac_str:>8} "
                f"{cvr_str:>7} "
                f"{row['spend_share']:>10.1f}%"
            )

      

       # print("\n  🏆  TOP 3 PLATFORM BY ROAS\n")
       # for _, row in platform_df.nlargest(3, "roas")[
       #     [ "platform", "platform_roas", ,"spend_share"]
       # ].iterrows():
         #   print(
          #      f"  {row['platform_roas']} "
         #       f"ROAS: {row['roas']:.2f}  "
           #     f"Spend Share: {row['spend_share']:.1f}%"
           # )

       
