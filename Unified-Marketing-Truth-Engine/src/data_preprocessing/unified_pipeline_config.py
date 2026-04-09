from dataclasses import dataclass
from typing import Optional

import pandas as pd

@dataclass(frozen=True)
class UnifiedAdsPipelineConfig:
    usecols: Optional[list[str]] = None
    parse_dates: bool = True
    fill_missing_metrics_with_zero: bool = True
    remove_duplicates: bool = True
    aggregate: bool = True
    compute_kpis: bool = True
    platform_col: str = "platform"
    group_by_date: bool = False
    time_granularity: Optional[str] = None
    sum_cols: Optional[list[str]] = None
    recompute_rates: bool = True
    campaign_objective: str = "Leads"