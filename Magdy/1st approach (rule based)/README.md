# Campaign Health Score POC

A pipeline that turns raw campaign metrics into a single health score, trend and confidence, diagnostic signals, and ranked top actions per campaign.

---

## Data source (default)

The pipeline uses **`global_ads_performance_dataset.csv`** by default. That file has one row per record with:

- **Columns:** `date`, `platform`, `campaign_type`, `industry`, `country`, `impressions`, `clicks`, `CTR`, `CPC`, `ad_spend`, `conversions`, `CPA`, `revenue`, `ROAS`

**How it’s used:** Each row is treated as **one campaign** (no grouping). Columns are mapped as: `impressions` → `impressions_30d`, `clicks` → `clicks_30d`, `conversions` → `conversions_30d`, `ad_spend` → `cost_30d`, `revenue` → `revenue_30d`. The same row is used for 7d metrics so `roas_trend` = 1. We add `quality_score=5`, `budget=cost_30d*1.2`. Pipeline step 1 then recomputes ROAS, CVR, CTR, CPA, AOV from the base fields.

To use the legacy **`campaign_data.csv`** instead (one row per campaign, pre-aggregated), call `load_data("campaign")` in code or change the loader in the notebook/app.

---

## Pipeline steps (explained)

### Step 1 — Load & validate data

- **No negative values:** Base metrics (impressions, clicks, conversions, cost, revenue) are clamped to ≥ 0.
- **No division by zero:** Ratios are computed only where denominators are non-zero; otherwise we get 0 or a safe default.
- **Canonical ratios** are always recomputed from base fields so the dataset is consistent:
  - **ROAS** = revenue / cost  
  - **CVR** = conversions / clicks  
  - **CTR** = clicks / impressions  
  - **CPA** = cost / conversions  
  - **AOV** = revenue / conversions  

Result: one clean canonical dataset.

---

### Step 2 — Compute percentiles

Raw metrics are turned into **relative strength** within the account using percentile rank (0–1):

- `roas_p`, `cvr_p`, `cpa_p`, `aov_p`, `ctr_p`, `qs_p` (quality score).

**CPA** is “lower is better,” so it is used later in the health formula as **1 − cpa_p** so that a lower CPA gives a higher contribution to the score.

---

### Step 3 — Compute trend signals

Recent (7d) vs longer-term (30d) behavior:

- **roas_trend** = roas_7d / roas_30d  
- **conversion_trend** = (conversions_7d / 7) vs (conversions_30d / 30), normalized  
- **spend_trend** = (cost_7d / 7) vs (cost_30d / 30), normalized  

All trends are **clipped between 0.5 and 1.5** to limit the impact of extreme noise.

---

### Step 4 — Compute confidence score

Low-conversion campaigns should not drive recommendations too strongly:

- **confidence** = min(1, conversions_30d / 30)

So campaigns with ≥ 30 conversions in 30 days get full confidence; below that, confidence scales down.

---

### Step 5 — Compute health score

A single **ROAS-focused** score (0–100) from percentile components:

- **HealthScore** = 0.40×roas_p + 0.20×cvr_p + 0.15×(1−cpa_p) + 0.10×aov_p + 0.10×ctr_p + 0.05×qs_p  

Then **trend adjustment**:

- **AdjustedScore** = HealthScore × (0.9 + 0.2×roas_trend), then scaled to 0–100 (with clipping).

Each campaign gets `health_score` and `adjusted_health_score`.

---

### Step 6 — Classify campaign state

Simple buckets for action routing:

- **adjusted_score > 75** → **Scale**  
- **50–75** → **Optimize**  
- **< 50** → **Fix**  

---

### Step 7 — Build diagnostic signals

Structured “reasons” to explain performance and guide actions:

- **Scaling signal:** high when roas_p > 0.7, roas_trend > 1.05, and budget utilization is high (e.g. ≥ 80%).
- **Efficiency problem:** high when roas_p < 0.4, cpa_p high, cvr_p low.
- **Creative problem:** high when ctr_p < 0.3 and impressions are relatively high.
- **Landing page signal:** high when ctr_p is high but cvr_p is low (clicks don’t convert).

These feed into which actions are suggested next.

---

### Step 8 — Build action scoring

For each campaign we score a set of actions (e.g. Increase Budget, Improve Ad Copy, Improve Landing Page, Reduce Budget/Pause, Optimize Bidding, Scale Campaign, Fix Creative & Landing). Each action has:

- An **eligibility rule** (e.g. “Increase Budget” only if roas_p > 0.6).
- A **score formula** (e.g. for “Increase Budget”: roas_p×0.5 + roas_trend×0.3 + confidence×0.2).

Actions are **ranked per campaign**; we keep the **top 3** as the main recommendations.

---

### Step 9 — Final output table

The POC result is a table with one row per campaign and columns such as:

**Campaign | Health | Trend | Confidence | State | Top Action 1 | Top Action 2 | Top Action 3**

---

### Step 10 — Visualize (Streamlit dashboard)

Optional dashboard that shows, per campaign:

- Health score (and state)
- Trend and confidence
- Budget utilization
- A simple “gauge” for health
- Metric percentiles (e.g. bar chart)
- Top 3 recommended actions
- Diagnostic signals (expandable)
- Full final table for all campaigns

---

## How to run

- **Notebook:** Open `main.ipynb` and run cells in order (load data → validate → run pipeline → final table).
- **CLI:** `python3 campaign_health.py` — runs the pipeline and prints the final table.
- **Dashboard:** `streamlit run app.py` — interactive health view and recommendations.

**Install:** `pip install pandas numpy streamlit` (or `uv sync` / `pip install -e .` from the project root).
