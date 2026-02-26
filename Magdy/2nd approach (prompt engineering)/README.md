# Campaign Recommendation Pipeline (POC)

This project is a small Python-based pipeline that turns **raw campaign metrics** into an **LLM-written campaign analysis and recommendations** using your custom prompt in `Prompt 1.txt`.

- **Input**: per-platform campaign data (CSV/DataFrame or list of dicts).
- **Processing**: feature reduction to basic metrics + ROAS computation per platform.
- **Prompting**: builds the JSON payload expected by `Prompt 1.txt` and sends it to an LLM.
- **Output**: the raw text response from either **Groq** or **OpenAI** (you can choose per call).

The core code lives in the `campaign_pipeline` package and is designed to be called from a notebook.

---

## 1. Setup

1. **Create and activate a virtual environment** (one called `.venv` is already used here):

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**

   You can use **Groq**, **OpenAI**, or both:

   - Groq:

     ```bash
     $env:GROQ_API_KEY = "<your_groq_api_key_here>"
     ```

   - OpenAI:

     ```bash
     $env:OPENAI_API_KEY = "<your_openai_api_key_here>"
     ```

   If you prefer, you can also put these in a local `.env` file (see `.env.example`) and load them in your notebook or entry script.

---

## 2. Expected input data

Each campaign row should include at least:

- `platform` (e.g., `"Google Ads"`, `"Meta"`)
- `objective` (e.g., `"Leads"`) – optional but recommended
- `impressions`
- `clicks`
- `conversions`
- `revenue`
- **`spend` _or_ `cost`** (the pipeline normalizes `cost` → `spend`)

You can pass data as:

- A `pandas.DataFrame`, or
- A list of Python dicts with these keys.

The pipeline groups by `platform` (and `objective` if present), sums the numeric metrics, and computes **ROAS = revenue / spend** when `spend > 0` (otherwise ROAS is left `None`).

---

## 3. Using the notebook

1. Launch Jupyter from the project root:

   ```bash
   jupyter notebook
   ```

2. Open `notebooks/campaign_recommendation_demo.ipynb`.
3. Run cells in order to:
   - Set the working directory to `campaign_pipeline`.
   - Create a sample `DataFrame` of campaign metrics.
   - Define `campaign_target` (goal + KPIs) and `business_domain` (industry, offering, audience, funnel stage).
   - Call `run_campaign_analysis` from `runner.py`.

Example call (Groq, default):

```python
from runner import run_campaign_analysis

result = run_campaign_analysis(
    campaign_data=sample_data,
    campaign_target=campaign_target,
    business_domain=business_domain,
    provider="groq",  # or "openai"
)

print(result)  # raw LLM output as text
```

If you use `provider="openai"`, the same call will go through the OpenAI Responses API instead of Groq.

---

## 4. How it works (modules)

- `transform.py`: normalizes columns, aggregates metrics per platform, computes ROAS.
- `data_model.py`: small dataclasses describing per-platform metrics.
- `prompt_payload.py`: builds the JSON payload structure expected by `Prompt 1.txt`.
- `openai_client.py`: sends the prompt + JSON payload to either Groq (`ChatGroq`) or OpenAI (`OpenAI().responses.create`) and returns the raw text.
- `runner.py`: orchestrates the full flow (`campaign_data` → metrics → payload → LLM call).

You can reuse `run_campaign_analysis` in other notebooks or scripts to analyze different campaigns or timeframes.
