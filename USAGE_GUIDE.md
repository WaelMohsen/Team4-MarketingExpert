# Operations & Usage Guide

This guide provides step-by-step instructions on how to execute every component of the Unified Marketing Truth Engine.

## 1. Prerequisites
Ensure your environment is set up:
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables in .env
OPENAI_API_KEY="your-api-key"
OPENAI_MODEL="gpt-4o-mini"
```

---

## 2. Running the Full Pipeline
The primary entry point is `run_pipeline.py`. It executes the full flow (Ingestion → Prep → Enrichment → Analysis → Recommendation → Evaluation) in a granular loop.

### Basic Run
```bash
python run_pipeline.py --input-csv data/raw/your_data.csv
```

### Controlled Testing (Row Limit)
To test the pipeline on a small subset of data (highly recommended for debugging):
```bash
python run_pipeline.py --input-csv data/raw/your_data.csv --row-limit 3
```

### Skip Evaluation
If you only want analysis results without running the AI auditor:
```bash
python run_pipeline.py --input-csv data/raw/your_data.csv --skip-evaluation
```

---

## 3. Running Standalone Evaluators
You can run the evaluators independently if you already have analysis or recommendation JSON files and want to grade them without re-running the entire pipeline.

### Analysis Evaluator
Grades a specific analysis report against raw campaign data, business domain, and campaign targets.
```bash
python -m src.modules.evaluation.analysis_evaluator
```
*Note: Ensure the file paths inside the script's `if __name__ == "__main__"` block point to your target JSON files.*

### Recommendation Evaluator
Grades recommendation cards against raw campaign data, business context, and analysis.
```bash
python -m src.modules.evaluation.recommendation_evaluator
```

---

## 4. Understanding Outputs
After a run, navigate to `data/outputs/`:
- **For global audit data**: Check `_global/run_TIMESTAMP/results/audit/`.
- **For specific campaign rows**: Check `campaign_N/run_TIMESTAMP/results/`.
- **For Logs**: All console output is duplicated at `logs/pipeline.log`.

---

## 5. Running Tests
The pipeline includes a comprehensive suite of unit and integration tests to ensure data integrity and engine stability.

### Run All Tests
```bash
python -m pytest tests/
```

### Run Tests with Coverage
```bash
python -m pytest tests/ --cov=src
```

### Run Specific Test Suites
```bash
# Core engine tests
python -m pytest tests/core/

# Shared utility tests
python -m pytest tests/shared/

# Pipeline module tests
python -m pytest tests/modules/preprocessing/
```

---

## 6. Troubleshooting
- **401 Unauthorized**: Check your API key in `.env`.
- **FileNotFoundError**: Ensure your `--input-csv` path is correct.
- **JSON Parsing Errors**: This usually happens if the LLM output was cut off (increase `max_output_tokens` in the module if needed).
