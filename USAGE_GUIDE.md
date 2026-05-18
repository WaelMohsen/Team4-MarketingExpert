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
python run_pipeline.py --input-csv data/domain_data/domain_dataset_ver_*.csv --row-limit 3
```

### Dynamic Campaign Grouping (Cohort Batching)
If your input CSV includes an `index` column (e.g. `data/domain_data/domain_dataset_ver_3.csv`), the pipeline dynamically groups rows sharing the same index into a single campaign cohort (labeled as `campaign_1`, `campaign_2`, etc.). This processes the campaign across different platforms and execution dates together, with campaign objectives derived from the first row of each cohort. 

If the `index` column is absent, the pipeline automatically falls back to standard chunk-based slicing of size `--batch-size` (default: 6).

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
*Note: Ensure the file paths inside the script's `if __name__ == "__main__"` block point to your target JSON files. The evaluator is robust enough to automatically load `enriched_summary.json` as a fallback if the target JSON lacks the full campaign context.*

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

## 5. Running the API
The pipeline can also be accessed via a REST API using FastAPI.

### Start the API Server
```bash
python -m src.api.app
```
By default, the server will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

### API Endpoints

#### POST `/api/v1/analysis`
Performs Stage 1 Analysis on campaign data.

**Sample Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
     -H "Content-Type: application/json" \
     -d '{
       "campaign_data": {
         "campaign_name": "Summer Sale",
         "platform": "Google Ads",
         "spend": 1250.50,
         "clicks": 450,
         "impressions": 12000,
         "conversions": 15,
         "conversion_value": 3000.00
       },
       "business_domain": {"industry": "SaaS"},
       "campaign_target": {"primary_goal": "efficiency"}
     }'
```

#### POST `/api/v1/recommendation`
Performs Stage 2 Recommendations based on analysis results and raw campaign metrics.

**Note:** If `analysis_results` is omitted, the API will automatically trigger the Stage 1 Analysis internally first.

**Sample Request (Automatic Analysis):**
```bash
curl -X POST "http://localhost:8000/api/v1/recommendation" \
     -H "Content-Type: application/json" \
     -d '{
       "campaign_data": {
         "campaign_name": "Summer Sale",
         "platform": "Google Ads",
         "spend": 1250.50,
         "clicks": 450,
         "impressions": 12000,
         "conversions": 15,
         "conversion_value": 3000.00
       },
       "business_domain": {"industry": "SaaS"},
       "campaign_target": {"primary_goal": "efficiency"}
     }'
```

**Sample Request (With Provided Analysis):**
```bash
curl -X POST "http://localhost:8000/api/v1/recommendation" \
     -H "Content-Type: application/json" \
     -d '{
       "analysis_results": {"analysis": {"executive_summary": "..."}},
       "campaign_data": { ... },
       "business_domain": {"industry": "SaaS"},
       "campaign_target": {"primary_goal": "efficiency"}
     }'
```

---

## 6. Running Tests
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
