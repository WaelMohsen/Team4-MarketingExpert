# Unified Marketing Truth Engine

Welcome to the unified version of the Marketing Truth Engine. This repository branch (`staging`) has been restructured to contain only the latest, consolidated, and working version of the project.

## Architecture & Contributions

This codebase is a combination of the best implementations from our contributors: **Sarah, Magdy, and Marwa**. The goal was to unify the architecture into a single, cohesive structure.

### 1. Sarah's Architecture (The Core Pipeline)
- **What was used:** We utilized Sarah's `v5` Object-Oriented architecture (`src/data_preprocessing` and `src/LLMs_and_Prompts`) as the foundation. Her `run_pipeline.py` serves as the robust main entry point.
- **Why:** Her approach utilized modern OOP principles, creating a robust, schema-validated data pipeline capable of seamless extraction, transformation, and prompt building. 

### 2. Magdy's Enhancements (Prompts & Notebooks)
- **What was used:** Magdy's core `Prompt 1.txt`, environment management system (`.env.example`), and Jupyter `notebooks/` directory.
- **Why:** Magdy provided the interactive Jupyter notebooks, which are excellent for demonstrating and testing the pipeline outside a strict script. Additionally, his `Prompt 1.txt` acts as the brain of the LLM integration. Setting up environment variables correctly was also guided by his conventions.

### 3. Marwa's Modularity Principles
- **What was used:** Marwa's project structure concepts. 
- **Why:** Marwa's work highlighted the need for single-responsibility modules (e.g., keeping data loading separate from metrics calculations and LLM clients). While Sarah's pipeline was used for the final execution flow, Marwa's principles heavily guided how the `src/` directory should be strictly separated by distinct responsibilities.

### 4. Feature Reduction Pipeline
- **What was added:** We integrated a native Pandas feature reduction mechanism (`usecols`) into the root `AdsDataLoader`.
- **Why:** To improve memory efficiency, speed, and reduce noise, the data loader now strictly extracts only the exact columns designated for the pipeline right at the source, ignoring everything else in the raw CSV. Following extraction, the data is immediately mapped to the uniform Schema using `canonicalize_columns`.

### 5. Two-Stage LLM Inference Engine
- **What was added:** The LLM prompt logic was decoupled from a single massive operation into a functional two-stage pipeline.
- **Why:** 
  1. **Stage 1 (Analysis)**: An Analyst persona ingests the raw JSON campaign metrics and outputs an objective, insight-driven `analysis` payload. It is restricted from giving recommendations.
  2. **Stage 2 (Recommendation)**: A Strategist persona ingests the `analysis` output from Stage 1, evaluates it against the Campaign targets and Business Domain, and deterministically outputs 5-8 highly actionable `recommendation` cards.
  This decoupling improves LLM reasoning, reduces token contamination, and creates modular outputs that can be audited individually.

## Expected Input Data

For the pipeline to correctly map metrics and compute KPIs, each campaign row in your source CSV should include at least:
- `platform` (e.g., `"Google Ads"`, `"Meta"`)
- `objective` (e.g., `"Leads"`) – optional but recommended
- `impressions`
- `clicks`
- `conversions`
- `revenue`
- **`spend` _or_ `cost`** (the pipeline automatically normalizes `cost` → `spend`)

The pipeline handles aggregating duplicate rows by `platform` (and `objective`), summing numeric metrics, and computing KPI features (like ROAS = revenue / spend).

## How to Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment:**
   Copy `.env.example` to `.env` and configure your API keys:
   ```bash
   OPENAI_API_KEY="<your_openai_api_key_here>"
   OPENAI_MODEL="gpt-4o-mini"
   ```

3. **Run the Pipeline:**
   The pipeline can be customized using CLI arguments:
   ```bash
   python run_pipeline.py \
       --input-csv data/raw/global_ads_performance_dataset.csv \
       --analysis-output data/outputs/analysis.json \
       --recommendations-output data/outputs/recommendations.json
   ```

4. **Explore the Notebooks:**
   Launch Jupyter and check out `notebooks/campaign_recommendation_demo.ipynb` for an interactive step-by-step interactive POC using identical modules.
   ```bash
   jupyter notebook
   ```
