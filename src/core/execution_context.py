from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import pandas as pd

@dataclass
class ExecutionContext:
    """
    Shared state container passed between modules in the pipeline.
    """
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Data states
    raw_df: Optional[pd.DataFrame] = None
    processed_df: Optional[pd.DataFrame] = None
    
    # Analysis & Enrichment results
    enriched_data: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    recommendation_results: Dict[str, Any] = field(default_factory=dict)
    
    # Evaluation results
    evaluations: Dict[str, Any] = field(default_factory=dict)
    
    # Path for row-specific persistence (e.g., campaign_1/)
    runtime_output_path: Optional[str] = None

    # Runtime info
    errors: list[str] = field(default_factory=list)

    def set_metadata(self, key: str, value: Any):
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)
