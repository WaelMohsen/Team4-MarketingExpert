import json
from pathlib import Path
from typing import Dict, Any

from src.unified_truth_engine import TruthEngineConfig, run_truth_engine


def main() -> Dict[str, Any]:
    """
    Convenience entrypoint for running the unified Truth Engine
    against the default sample dataset.
    """
    config = TruthEngineConfig(
        data_path=Path("Data/raw/global_ads_performance_dataset.csv"),
        provider="openai",
        model="gpt-5-mini",
        campaign_objective="Leads",
        primary_goal="increase qualified leads",
        kpis=["leads", "cpl"],
        industry="Retail",
        offering="Membership plan",
        audience="People shopping for monthly essentials",
        funnel_stage="conversion",
    )

    result = run_truth_engine(config)

    # Persist prompt messages for inspection
    with open("Data/outputs/messages.json", "w", encoding="utf-8") as f:
        json.dump(result["messages"], f, ensure_ascii=False, indent=2)

    print("\n=== PLATFORM SUMMARY ===\n")
    print(json.dumps(result["platform_summary"], ensure_ascii=False, indent=2))

    print("\n=== TOTALS ===\n")
    print(json.dumps(result["totals"], ensure_ascii=False, indent=2))

    print("\n=== LLM JSON RESPONSE ===\n")
    print(json.dumps(result["llm_response"], ensure_ascii=False, indent=2))

    return result


if __name__ == "__main__":
    main()
