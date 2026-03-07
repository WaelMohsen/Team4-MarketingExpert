"""
main.py — Truth Engine entry point.

Usage:
    python main.py

Phases:
    Phase 1 — DataLoader + MetricsCalculator
    
"""

import json
import os

from src.data_loader               import DataLoader
from src.metrics_calculator        import MetricsCalculator
from src.transform          import DataTransformer
from src.openai_client import OpenAIClient

DATA_PATH        = "data/ads_performance.csv"

def run():
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║         MARKETING TRUTH ENGINE  v1        ║")
    print("║         Phase 1   ║")
    print("╚══════════════════════════════════════════════╝")

    os.makedirs("output", exist_ok=True)

    # ── Phase 1: Load data & calculate metrics ─────────────────────────────────
   # loader      = DataLoader(DATA_PATH)
   # df          = loader.load()
   # calculator  = MetricsCalculator(df)
   # results     = calculator.calculate()
    #transformer = DataTransformer(results)
   # transformer.to_json("prompt engineering/campaign_platforms_data.json")
    client = OpenAIClient() 
    message= client._creat_message(client._prompt_path, client._input_path)
    recomenditions=client._call_api(message)
    print(recomenditions)


 

if __name__ == "__main__":
    run()
