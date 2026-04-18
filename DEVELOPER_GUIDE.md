# Marketing Truth Engine: Developer Guide (Strictly Granular)

This guide explains the granular architecture and development standards for the Marketing Truth Engine.

## 📐 Architectural Philosophy: Strict Granularity
Unlike traditional marketing tools that aggregate data into high-level averages, this engine processes every campaign (row) as a **self-contained case study**.

### Benefits:
- **No Data Leakage**: Row 1 performance never influences the analysis of Row 2.
- **Auditability**: Every row has a clear audit trail from raw data to evaluation grade.
- **Precision**: LLMs can focus on specific metadata (audience, industry) for a single campaign.

---

## 🏗️ Intelligence Workflow

### 1. Preparation (Batch Preparation)
- **`IngestionModule`**: Loads the source file.
- **`PreprocessingModule`**: Cleans, standardizes columns, and removes duplicates.
- **Output**: A global `processed_data.csv` saved in the `audit/` folder of the current run.

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
The quality of the AI output is audited by a separate LLM process using the exact same unified context (Data, Target, Domain) used during generation to ensure absolute accuracy. Results are split into two files:
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
- Avoid `groupby` or `sum()` logic within intelligence modules.
- Assume the input is a **single-row DataFrame**.
- Use `context.runtime_output_path` for all `save()` operations to ensure data ends up in the correct `campaign_{i}/` folder.

### 3. Response Schemas
- Define all LLM output formats in `src/shared/models/llm_responses.py`.
- Use the `LLMApiClient.generate_json()` method to automatically validate outputs against these Pydantic models.

---

## 📂 Run Directory Anatomy
```text
data/outputs/run_YYYYMMDD_HHMM/
├── audit/                  # Global cleaned CSV
├── campaign_1/             # Isolated results for Row 1
│   ├── enriched_summary.json
│   ├── analysis_result.json
│   ├── recommendation_result.json
│   ├── analysis_evaluation_results.json
│   └── recommendation_evaluation_results.json
└── campaign_2/             # Isolated results for Row 2
```
