from dataclasses import dataclass
from typing import Dict, Literal, Optional


Platform = Literal["meta", "google", "linkedin", "pinterest"]

# @dataclass utomatically generates boilerplate methods (__init__, __repr__, __eq__)
# __repr__ — Developer Representation. Defines how the object looks when printed or inspected.
# __eq__ — Equality Comparison. Defines how == works for your objects.
# frozen = True It makes the instance immutable after creation. You cannot modify attributes. Any attempt to assign a new value raises an error.
# Ensures configuration integrity. Prevents accidental mutation Makes objects hashable (can be used in sets/dicts)

@dataclass(frozen=True)
class PlatformFieldMapping:
    """
    Holds platform-specific column names and maps them into unified names.
    Example: "Amount Spent (USD)" -> "spend"
    """
    platform: Platform
    column_map: Dict[str, str]  # raw_column_name -> unified_column_name
    currency: Optional[str] = None
    timezone: Optional[str] = None


# Raw platform labels -> unified platform value
# Example: "Facebook Ads" -> "meta"
PLATFORM_VALUE_ALIASES: Dict[str, Platform] = {
    "meta": "meta",
    "facebook": "meta",
    "facebook ads": "meta",
    "fb": "meta",
    "instagram": "meta",
    "instagram ads": "meta",
    "google": "google",
    "google ads": "google",
    "adwords": "google",
    "linkedin": "linkedin",
    "linkedin ads": "linkedin",
    "pinterest": "pinterest",
    "pinterest ads": "pinterest",
}


def normalize_platform_value(value: str) -> Platform:
    """
    Normalize raw platform values to unified values used by the project.
    Example: 'Facebook Ads' -> 'meta'
    """
    key = str(value).strip().lower()
    if key in PLATFORM_VALUE_ALIASES:
        return PLATFORM_VALUE_ALIASES[key]
    raise ValueError(
        f"Unsupported platform value '{value}'. Expected aliases for: meta/google/linkedin/pinterest."
    )


def get_default_platform_mappings() -> Dict[Platform, PlatformFieldMapping]:
    """
    Default column mappings for common exports from supported ad platforms.
    Extend or override these mappings for your own account export formats.
    """
    return {
        "meta": PlatformFieldMapping(
            platform="meta",
            column_map={
                "Date": "date",
                "Day": "date",
                "Campaign name": "campaign_name",
                "Campaign Name": "campaign_name",
                "Campaign": "campaign_name",
                "Campaign ID": "campaign_id",
                "Ad set name": "adset_name",
                "Ad Set Name": "adset_name",
                "Ad set ID": "adset_id",
                "Ad name": "ad_name",
                "Ad Name": "ad_name",
                "Ad ID": "ad_id",
                "Account ID": "account_id",
                "Impressions": "impressions",
                "Reach": "reach",
                "Frequency": "frequency",
                "Clicks (all)": "clicks",
                "Link clicks": "clicks",
                "Amount spent (USD)": "spend",
                "Amount spent": "spend",
                "Purchases": "conversions",
                "Results": "conversions",
                "Website purchases conversion value": "conversion_value",
                "Purchase conversion value": "conversion_value",
            },
        ),
        "google": PlatformFieldMapping(
            platform="google",
            column_map={
                "Date": "date",
                "Day": "date",
                "Campaign": "campaign_name",
                "Campaign name": "campaign_name",
                "Campaign ID": "campaign_id",
                "Campaign type": "campaign_type",
                "Ad group": "adset_name",
                "Ad group name": "adset_name",
                "Ad group ID": "adset_id",
                "Ad ID": "ad_id",
                "Account": "account_id",
                "Customer ID": "account_id",
                "Impr.": "impressions",
                "Impressions": "impressions",
                "Clicks": "clicks",
                "Cost": "spend",
                "Cost / conv.": "cpa",
                "Conversions": "conversions",
                "Conv. value": "conversion_value",
                "Conversion value": "conversion_value",
            },
            currency="USD",
        ),
        "linkedin": PlatformFieldMapping(
            platform="linkedin",
            column_map={
                "Start Date": "date",
                "Date": "date",
                "Campaign Name": "campaign_name",
                "Campaign": "campaign_name",
                "Campaign ID": "campaign_id",
                "Campaign Group Name": "campaign_group_name",
                "Creative Name": "ad_name",
                "Creative ID": "ad_id",
                "Account Name": "account_name",
                "Account ID": "account_id",
                "Impressions": "impressions",
                "Clicks": "clicks",
                "Spend": "spend",
                "Cost in Local Currency": "spend",
                "Conversions": "conversions",
                "Conversion Value": "conversion_value",
            },
        ),
        "pinterest": PlatformFieldMapping(
            platform="pinterest",
            column_map={
                "Date": "date",
                "Campaign name": "campaign_name",
                "Campaign Name": "campaign_name",
                "Campaign ID": "campaign_id",
                "Ad group name": "adset_name",
                "Ad group ID": "adset_id",
                "Pin name": "ad_name",
                "Pin ID": "ad_id",
                "Ad account ID": "account_id",
                "Impressions": "impressions",
                "Clicks": "clicks",
                "Spend in account currency": "spend",
                "Spend": "spend",
                "Conversions": "conversions",
                "Total conversion value": "conversion_value",
                "Conversion value": "conversion_value",
            },
        ),
    }
