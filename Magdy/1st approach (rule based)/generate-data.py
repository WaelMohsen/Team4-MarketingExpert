import numpy as np
import pandas as pd

np.random.seed(42)

n_campaigns = 50

campaigns = []

for i in range(n_campaigns):
    
    impressions = np.random.randint(10000, 200000)
    
    ctr = np.random.uniform(0.01, 0.08)  # 1%–8%
    clicks = impressions * ctr
    
    cvr = np.random.uniform(0.01, 0.12)  # 1%–12%
    conversions = clicks * cvr
    
    cpc = np.random.uniform(0.3, 3.0)
    cost = clicks * cpc
    
    aov = np.random.uniform(50, 300)
    revenue = conversions * aov
    
    roas = revenue / cost if cost > 0 else 0
    cpa = cost / conversions if conversions > 0 else 0
    
    quality_score = np.random.randint(3, 10)
    
    budget = np.random.randint(1000, 20000)
    
    bidding_strategy = np.random.choice([
        "Maximize Conversions",
        "Target CPA",
        "Maximize Clicks",
        "Target ROAS"
    ])
    
    # 7-day trend simulation
    roas_7d = roas * np.random.uniform(0.7, 1.3)
    conversions_7d = conversions * np.random.uniform(0.6, 1.4)
    cost_7d = cost * np.random.uniform(0.6, 1.4)
    
    campaigns.append([
        i,
        f"Campaign_{i}",
        impressions,
        clicks,
        conversions,
        cost,
        revenue,
        ctr,
        cvr,
        cpa,
        roas,
        aov,
        quality_score,
        budget,
        bidding_strategy,
        roas_7d,
        conversions_7d,
        cost_7d
    ])

columns = [
    "campaign_id",
    "campaign_name",
    "impressions_30d",
    "clicks_30d",
    "conversions_30d",
    "cost_30d",
    "revenue_30d",
    "ctr_30d",
    "cvr_30d",
    "cpa_30d",
    "roas_30d",
    "aov_30d",
    "quality_score",
    "budget",
    "bidding_strategy",
    "roas_7d",
    "conversions_7d",
    "cost_7d"
]

df = pd.DataFrame(campaigns, columns=columns)

df.head()
df.to_csv("campaign_data.csv", index=False)