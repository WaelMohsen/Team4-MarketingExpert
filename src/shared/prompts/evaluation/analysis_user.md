# Campaign Analysis Evaluation Prompt

Please evaluate the following campaign analysis report.


## 1. Campaign Goal and KPIs

**Primary Goal:**  
{{PRIMARY_GOAL}}

**KPIs:**  
{{KPIS}}


## 2. Campaign Context (Target & Domain)

{{CAMPAIGN_CONTEXT}}


## 3. Raw Campaign Data

{{RAW_DATA}}


## 4. Generated Analysis Report (To Evaluate)

{{ANALYSIS_REPORT}}


# Your Evaluation Process

## Step 1 — Hallucination Check

Run the hallucination checklist from your system prompt against the report.

- List each checklist item  
- Mark each as **Pass** or **Fail**  
- Any failure must be reflected in the *Hallucination score*

## Step 2 — KPI Alignment Check

Confirm whether the report explicitly addresses:

- The **Primary Goal:** {{PRIMARY_GOAL}}  
- **Each KPI:** {{KPIS}}  
- Whether **null KPI fields are flagged**, and whether their absence is explained in business terms  


## Step 3 — Score Each Criterion

For each of the 5 criteria, provide:

- A **score (1–5)**  
- A **one-sentence reasoning** citing a specific part of the report  
- The **exact evidence from raw data** used to verify or refute the claim  


## Step 4 — Apply Verdict Rules

- State the **total score**  
- Apply verdict rules **mechanically** as defined in your system prompt  