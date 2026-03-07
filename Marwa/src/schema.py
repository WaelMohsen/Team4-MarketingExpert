"""
schema.py — Internal data schema for the Truth Engine.

Defines:
- Required raw CSV columns
- Column mapping from raw → internal names
- Internal column types
- Derived metric column names
"""

# ── Raw CSV columns we expect ──────────────────────────────────────────────────
REQUIRED_COLUMNS = [
    "campaign_id",
    "platform",
    "date",
    "spend",
    "impressions",
    "clicks",
    "conversions",
    "revenue",
]

# ── Map raw column names → internal names ─────────────────────────────────────
# Extend this if the real Kaggle CSV uses different field names.
COLUMN_MAP = {
    "campaign_id":  "campaign_id",
    "platform":     "platform",
    "date":         "date",
    "spend":        "spend",
    "impressions":  "impressions",
    "clicks":       "clicks",
    "conversions":  "conversions",
    "revenue":      "revenue",
    
}

# ── Internal column dtypes (used by data_loader for casting) ──────────────────
COLUMN_TYPES = {
    "campaign_id":  str,
    "platform":     str,
    "date":         str,   # kept as string; parsed to date where needed
    "spend":        float,
    "impressions":  int,
    "clicks":       int,
    "conversions":  int,
    "revenue":      float,
}

# ── Derived metric columns added by metrics_calculator ────────────────────────
METRIC_COLUMNS = [
    "roas",          # Return on Ad Spend = revenue / spend
    "cac",           # Cost to Acquire a Customer = spend / conversions
    "cvr",           # Conversion Rate % = conversions / clicks * 100
    "ctr",           # Click-Through Rate % = clicks / impressions * 100
    "spend_share",   # % of total spend this campaign accounts for
]

# ── Normalised platform name map ──────────────────────────────────────────────
PLATFORM_NAME_MAP = {
    "meta":     "Meta",
    "facebook": "Meta",
    "fb":       "Meta",
    "google":   "Google",
    "google ads": "Google",
    "tiktok":   "TikTok",
    "tik tok":  "TikTok",
}
