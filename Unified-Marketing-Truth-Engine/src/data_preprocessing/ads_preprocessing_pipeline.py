from typing import Optional, Union
import pandas as pd

from .ads_preprocessor import AdsPreprocessor
from .ads_schema import UnifiedAdsSchema
from src.feature_extraction.ads_kpi_features import AdsKpiFeatures
from .data_loader import AdsDataLoader, Source

class UnifiedAdsPipeline:
    """
    Public API:
      transform() = read -> map -> validate -> check data types -> remove duplicates -> compute KPIs -> convert to JSON
    """

    def __init__(self, preprocessor: AdsPreprocessor, schema: UnifiedAdsSchema):
        self.preprocessor = preprocessor
        self.schema = schema
        self.loader = AdsDataLoader()

    def transform(
        self,
        source: Source, *,
        parse_dates: bool = True,
        fill_missing_metrics_with_zero: bool = True,
        remove_duplicates: bool = True,
        aggregate: bool = True,
        compute_kpis: bool =True,
        platform_col: Optional[str] = "platform", 
        group_by_date: bool = False, 
        time_granularity: bool= None, 
        sum_cols: bool = None, 
        recompute_rates: bool = True,
        campaign_objective: Optional[str] ="Leads"
        ) -> pd.DataFrame:
        df = self.loader.load(source)  # dataframe becomes "source": DataFrame or path

        self.schema.validate_required(df)

        df = self.preprocessor.enforce_types(
            df,
            parse_dates=parse_dates,
            fill_missing_metrics_with_zero=fill_missing_metrics_with_zero,
        )

        if remove_duplicates:
            df = self.preprocessor.remove_duplicates(df)

        if aggregate:
            df = self.preprocessor.aggregate_single_campaign(df, 
                                           platform_col = "platform", 
                                           group_by_date = False, 
                                           time_granularity= None, 
                                           sum_cols = None)
            
        if compute_kpis:
            df = AdsKpiFeatures.compute_kpis(df) 
        #print(df)
        
        df = self.preprocessor.convert_to_json(df,campaign_objective=campaign_objective)
                   
        
        return df