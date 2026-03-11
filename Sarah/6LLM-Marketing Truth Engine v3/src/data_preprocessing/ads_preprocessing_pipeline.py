from typing import Optional, Union
import pandas as pd

from .ads_preprocessor import AdsPreprocessor
from .ads_schema import UnifiedAdsSchema
from src.feature_extraction.ads_kpi_features import AdsKpiFeatures
from .data_loader import AdsDataLoader, Source


class UnifiedAdsPipeline:
    """
    Public API:
      - transform_to_df() = read -> map -> validate -> check data types
                             -> remove duplicates -> aggregate -> compute KPIs
      - transform()       = transform_to_df() -> convert to JSON
    """

    def __init__(self, preprocessor: AdsPreprocessor, schema: UnifiedAdsSchema):
        self.preprocessor = preprocessor
        self.schema = schema
        self.loader = AdsDataLoader()

    def transform_to_df(
        self,
        source: Source,
        *,
        parse_dates: bool = True,
        fill_missing_metrics_with_zero: bool = True,
        remove_duplicates: bool = True,
        aggregate: bool = True,
        compute_kpis: bool = True,
        platform_col: Optional[str] = "platform",
        group_by_date: bool = False,
        time_granularity: Optional[str] = None,
        sum_cols: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        End-to-end data preparation that returns an aggregated DataFrame.

        This keeps the same logical steps as transform(), but stops
        before converting to the JSON payload structure so that
        downstream components (e.g. health scoring, platform summaries)
        can operate on the tabular data.
        """
        df = self.loader.load(source)

        self.schema.validate_required(df)

        df = self.preprocessor.enforce_types(
            df,
            parse_dates=parse_dates,
            fill_missing_metrics_with_zero=fill_missing_metrics_with_zero,
        )

        if remove_duplicates:
            df = self.preprocessor.remove_duplicates(df)

        if aggregate:
            df = self.preprocessor.aggregate_single_campaign(
                df,
                platform_col=platform_col or "platform",
                group_by_date=group_by_date,
                time_granularity=time_granularity,
                sum_cols=sum_cols,
            )

        if compute_kpis:
            df = AdsKpiFeatures.compute_kpis(df)

        return df

    def transform(
        self,
        source: Source,
        *,
        parse_dates: bool = True,
        fill_missing_metrics_with_zero: bool = True,
        remove_duplicates: bool = True,
        aggregate: bool = True,
        compute_kpis: bool = True,
        platform_col: Optional[str] = "platform",
        group_by_date: bool = False,
        time_granularity: Optional[str] = None,
        sum_cols: Optional[list[str]] = None,
        campaign_objective: Optional[str] = "Leads",
    ) -> list[dict]:
        """
        Backwards-compatible wrapper that returns the JSON-ready
        campaign_platforms_data structure expected by the prompting layer.
        """
        df = self.transform_to_df(
            source,
            parse_dates=parse_dates,
            fill_missing_metrics_with_zero=fill_missing_metrics_with_zero,
            remove_duplicates=remove_duplicates,
            aggregate=aggregate,
            compute_kpis=compute_kpis,
            platform_col=platform_col,
            group_by_date=group_by_date,
            time_granularity=time_granularity,
            sum_cols=sum_cols,
        )

        return self.preprocessor.convert_to_json(
            df, campaign_objective=campaign_objective or "Leads"
        )