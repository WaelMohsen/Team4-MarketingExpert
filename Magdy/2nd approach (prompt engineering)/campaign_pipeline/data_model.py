from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Metrics:
    spend: Optional[float] = None
    impressions: Optional[float] = None
    reach: Optional[float] = None
    clicks: Optional[float] = None
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    conversions: Optional[float] = None
    conversion_rate: Optional[float] = None
    cpa: Optional[float] = None
    revenue: Optional[float] = None
    roas: Optional[float] = None
    leads: Optional[float] = None
    cpl: Optional[float] = None
    video_views: Optional[float] = None
    engagements: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        return {
            "spend": self.spend,
            "impressions": self.impressions,
            "reach": self.reach,
            "clicks": self.clicks,
            "ctr": self.ctr,
            "cpc": self.cpc,
            "conversions": self.conversions,
            "conversion_rate": self.conversion_rate,
            "cpa": self.cpa,
            "revenue": self.revenue,
            "roas": self.roas,
            "leads": self.leads,
            "cpl": self.cpl,
            "video_views": self.video_views,
            "engagements": self.engagements,
        }


@dataclass
class PlatformMetrics:
    platform: str
    objective: Optional[str]
    metrics: Metrics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "objective": self.objective,
            "metrics": self.metrics.to_dict(),
        }


PlatformMetricsList = List[PlatformMetrics]
