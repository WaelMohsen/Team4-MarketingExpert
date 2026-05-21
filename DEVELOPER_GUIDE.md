# Marketing Truth Engine: Developer Guide (Strictly Granular)

This guide explains the granular architecture and development standards for the Marketing Truth Engine.

## 📐 Architectural Philosophy: Campaign Cohort Granularity
Unlike traditional marketing tools that aggregate the entire advertising account into high-level averages, this engine processes every campaign cohort as a **self-contained case study**. 
- A campaign cohort represents the **same campaign** tracked across multiple time periods and platforms (e.g. Google Ads, TikTok Ads, Meta Ads).
- **Dynamic Campaign Cohorts**: If the source data contains an `index` column, the engine groups rows sharing the same index into a single cohort. If the `index` column is absent, it falls back to standard chunk-based batching.
- **Goals and Objectives**: The goals, target audience, industry, and offering are derived from the *first row* of the campaign cohort (the source of truth), ensuring the entire campaign is analyzed under the correct strategic context.

### Benefits:
- **Platform Comparison**: Evaluates cross-channel performance (comparing Google Ads, TikTok Ads, Meta Ads) for the same campaign.
- **Temporal Analysis**: Tracks campaign metrics over time to identify trends, fatigue, and stability.
- **Precision**: LLMs focus on specific metadata for a cohesive campaign cohort rather than isolated individual rows.

---

## 🏗️ Intelligence Workflow

### 1. Preparation (Batch Preparation)
- **`IngestionModule`**: Loads the source file.
- **`PreprocessingModule`**: Cleans, standardizes columns, and removes duplicates.
- **Output**: A global `processed_data.csv` saved in the `_global/run_TIMESTAMP/results/audit/` folder.

### 2. Granular Iteration (The Engine Loop)
For each row, a new `ExecutionContext` is created, and the following stages are executed:

#### A. Enrichment (`campaign_data`)
The system flattens the row into a high-density JSON object. This object includes:
- **Identity**: Industry, Audience, Offering, Funnel Stage.
- **Metrics**: Standardized Performance KPIs (ROAS, CPA, CTR, etc.).
- **Diagnostics**: Pre-calculated signals like "high spend, low conversion".

#### B. Intelligence (Analysis & Recommendation)
- Uses **Pydantic Models** (`AnalysisResponse`, `RecommendationResponse`) to ensure LLM outputs are structured and valid.
- Prompts are loaded from the **Centralized Registry**.
- Both stages operate with **unified 360-degree context**, receiving the Raw Campaign Data, Business Domain, Campaign Targets, and Previous AI Results (for recommendations) to prevent any blind spots.

#### C. Evaluation (Split Grading)
The quality of the AI output is audited by a separate LLM process using the exact same unified context (Data, Target, Domain) used during generation to ensure absolute accuracy. If the generated output files (e.g., `analysis_result.json`) are missing original context fields like `campaign_data`, the evaluator will automatically fallback to loading `enriched_summary.json` from the same campaign run directory to reconstruct the full context. Results are split into two files:
- `analysis_evaluation_results.json`
- `recommendation_evaluation_results.json`

---

## 🛠️ Developer Standards

### 1. Managing Prompts
**Never hardcode `.txt` paths** in your modules.
- **To add a new prompt**:
    1. Place the file in `src/shared/prompts/`.
    2. Add a new key-value pair to `src/shared/utils/prompt_registry.py`.
    3. Access it in your module via `PromptRegistry.YOUR_KEY.value`.

### 2. Handling Data
- Intelligence modules receive a multi-row DataFrame (campaign cohort) representing the same campaign across platforms and time.
- The `EnrichmentModule` processes each row in the cohort individually using `build_platform_summary()` and collects them as a list of dicts.
- Use `context.runtime_output_path` for all `save()` operations to ensure data ends up in the correct campaign/batch results folder.

### 3. Response Schemas
- Define all LLM output formats in `src/shared/models/llm_responses.py`.
- Use the `LLMApiClient.generate_json()` method to automatically validate outputs against these Pydantic models.

---

## 🧪 Testing Standards
The project uses `pytest` for automated testing. Ensuring high test coverage is critical for maintaining engine reliability in granular processing.

### 1. Test Organization
- Test files must mirror the `src/` directory structure under `tests/`.
- File names must be prefixed with `test_` (e.g., `tests/core/test_pipeline_engine.py`).

### 2. Mocking Guidelines
- **Always mock API calls**: Use `monkeypatch` or `unittest.mock.patch` to isolate `LLMApiClient` calls. Never run actual LLM calls in the unit test suite.
- **Fixtures**: Use `tests/conftest.py` for shared fixtures like `empty_context` or `mock_campaign_data`.

### 3. Writing New Tests
- When adding a new module or utility, create a corresponding test file in `tests/`.
- Aim for at least 80% line coverage for new code.

---

```text
data/outputs/
├── _global/
│   └── run_YYYYMMDD_HHMM/
│       └── results/
│           └── audit/                  # Global cleaned CSV
├── campaign_1/                         # Isolated results for Row 1
│   └── run_YYYYMMDD_HHMM/
│       └── results/
│           ├── enriched_summary.json
│           ├── analysis_result.json
│           ├── recommendation_result.json
│           ├── analysis_evaluation_results.json
│           └── recommendation_evaluation_results.json
└── campaign_2/                         # Isolated results for Row 2
```
