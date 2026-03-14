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

## How to Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment:**
   Copy `.env.example` to `.env` and configure your API keys (e.g., `OPENAI_API_KEY` or `GROQ_API_KEY`).

3. **Run the Pipeline:**
   ```bash
   python run_pipeline.py
   ```

4. **Explore the Notebooks:**
   Launch Jupyter and check out `notebooks/` for interactive step-by-step demonstrations.
