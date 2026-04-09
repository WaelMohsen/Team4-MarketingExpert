# Unified Marketing Truth Engine

A modular Python pipeline that converts raw paid media performance data into structured, business-friendly LLM outputs in two stages:
1. analysis (what happened and why it matters)
2. recommendations (what to do next)

The project is organized as a layered architecture under `src/` with a CLI entrypoint in `run_pipeline.py`.

## What This Application Does

- Ingests ads data from file or DataFrame input.
- Normalizes and validates a unified schema.
- Enforces types, de-duplicates, aggregates by platform, and computes KPI features.
- Converts processed rows into a strict JSON payload for prompting.
- Runs a 2-stage LLM workflow:
  - Stage 1: structured performance analysis
  - Stage 2: structured recommendation cards
- Saves machine-readable JSON artifacts for downstream use.

## Architecture Layers

```mermaid
flowchart LR
    A[CLI Entrypoint\nrun_pipeline.py] --> B[Data Preprocessing Layer\nsrc/data_preprocessing]
    B --> C[Feature Layer\nsrc/feature_extraction]
    C --> D[Prompting Layer\nsrc/LLMs_and_Prompts]
    D --> E[LLM Inference Layer\nOpenAI Chat Completions]
    E --> F[Artifacts\nanalysis.json + recommendations.json]
```

### Layer Responsibilities

- `src/data_preprocessing`
  - `AdsDataLoader`: reads `.csv`, `.xlsx`, `.xls`, `.json`, `.parquet`.
  - `UnifiedAdsSchema`: required-column and numeric validations, alias model.
  - `AdsPreprocessor`: type casting, dedupe, aggregation, JSON conversion.
  - `UnifiedAdsPipeline`: orchestrates transform steps.

- `src/feature_extraction`
  - `AdsKpiFeatures`: computes `ctr`, `cpc`, `cpm`, `cvr`, `cpa`, `roas` where possible.
  - `AdsFeatureExtractor`: optional diagnostics and grouped extraction utilities.

- `src/LLMs_and_Prompts`
  - `PromptLoader`: loads prompt templates from module folder.
  - `PromptBuilder`: injects runtime data into template placeholders.
  - `structured_outputs.py`: Pydantic output contracts for stage 1 and stage 2.
  - `LLMApiClient`: OpenAI wrapper for text and schema-parse JSON.

- `tests`
  - `recommendation_response_eval.py`: DSPy-based quality evaluator for recommendation cards.

## End-to-End Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as run_pipeline.py
    participant P as UnifiedAdsPipeline
    participant B as PromptBuilder
    participant L as LLMApiClient

    U->>R: python run_pipeline.py
    R->>P: transform(input_csv, usecols, compute_kpis=True)
    P-->>R: campaign_platforms_data (JSON-ready list)

    R->>B: build_analysis_prompt(..., campaign_platforms_data)
    B-->>R: analysis_messages
    R->>L: generate_json(analysis_messages, AnalysisResponse)
    L-->>R: analysis_result
    R->>R: save analysis.json

    R->>B: build_recommendation_prompt(..., analysis_result)
    B-->>R: recommendation_messages
    R->>L: generate_json(recommendation_messages, RecommendationResponse)
    L-->>R: recommendation_result
    R->>R: save recommendations.json
```

## Input Data Contract

Minimum columns expected by the current pipeline run path:

- `date`
- `platform`
- `campaign_type`
- `impressions`
- `clicks`
- `spend`
- `conversions`
- `revenue` (loaded by default in `run_pipeline.py`, but see constraints section)

Also supported at schema/KPI level when present:

- `conversion_value`
- `reach`
- `frequency`
- optional IDs for deduping (`account_id`, `campaign_id`, `adset_id`, `ad_id`)

## LLM Contracts

### Stage 1 Output

`AnalysisResponse`:
- `analysis.executive_summary`
- `analysis.budget_and_efficiency[]`
- `analysis.results_and_value[]`
- `analysis.cross_channel_patterns_and_risks[]`
- `analysis.channel_notes[]`
- `analysis.missing_info[]`

### Stage 2 Output

`RecommendationResponse`:
- `recommendations[]` where each card includes:
  - `title`
  - `whats_happening`
  - `what_you_should_do[]`
  - `why_this_matters`
  - `priority`
  - `expected_impact`
  - `owner_suggestion`

## Project Structure

```text
Unified-Marketing-Truth-Engine/
  data/
    raw/
    outputs/
  logs/
  notebooks/
  src/
    data_preprocessing/
    feature_extraction/
    LLMs_and_Prompts/
    modeling/
    utils/
  tests/
  run_pipeline.py
  requirements.txt
  .env.example
```

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
copy .env.example .env
```

Set at least:

```env
OPENAI_API_KEY="<your_api_key>"
OPENAI_MODEL="gpt-5-mini"
```

Note: `.env.example` also includes `GROQ_API_KEY`, but the current pipeline uses OpenAI only.

## Run the Pipeline

```bash
python run_pipeline.py \
  --input-csv data/raw/global_ads_performance_dataset.csv \
  --analysis-output data/outputs/analysis.json \
  --recommendations-output data/outputs/recommendations.json
```

Generated artifacts:

- `data/outputs/analysis.json`
- `data/outputs/recommendations.json`

## Run Recommendation Evaluation (Optional)

```bash
python tests/recommendation_response_eval.py
```

Outputs:

- console ranking summary
- `logs/evaluation_results.json`
- `logs/evaluation.log`

## Constraints and Known Gaps (Current Code)

- `UnifiedAdsSchema.canonicalize_columns()` currently builds `rename_map` but does not apply a rename operation; alias canonicalization is not fully active in runtime.
- `run_pipeline.py` loads `revenue`, while KPI ROAS logic expects `conversion_value`; this can leave `revenue` and `roas` null in JSON output unless preprocessing is adjusted.
- `UnifiedAdsPipeline.transform()` currently hardcodes aggregation args (`platform`, no date grouping), even if optional parameters are passed.
- `AdsPreprocessor.aggregate_single_campaign()` contains a `group_keys` initialization ordering bug when `group_by_date=True`; default run path uses `False`, so this is not triggered in standard CLI execution.
- Prompt files `Prompt 1.txt` and `Prompt 2.txt` are legacy alternatives and are not used by the default CLI path.
- There is no automated unit test suite for pipeline transforms yet; existing `tests/` content focuses on LLM recommendation evaluation.

## Suggested Next Engineering Steps

1. Fix schema alias canonicalization (`rename(columns=rename_map)` and duplicate handling after rename).
2. Standardize value column naming (`revenue` vs `conversion_value`) across pipeline and KPI computation.
3. Make `transform()` honor passed aggregation parameters rather than hardcoded defaults.
4. Add unit tests for schema validation, KPI calculations, and aggregation edge cases.
5. Add a lightweight CI check to validate sample input -> output schema compliance.
