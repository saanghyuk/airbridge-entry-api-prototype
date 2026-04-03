"""
Generate weekly_YYYY-MM-DD.csv (1000 users) — represents "this week's new users"
and regenerate rct_data.csv (8000 users) — Phase 1 initial RCT data.

Files are saved to data/{app_name}/ directory:
  - weekly_YYYY-MM-DD.csv (dated, accumulates over time)
  - rct_data.csv (fixed, one-time)

ALL users have: UA features, In-app features, assigned_trigger, modal_clicked,
first_session_purchase, d3_purchase, d3_churn.

20% are randomly assigned (is_random=1), 80% are model-recommended (is_random=0).
Model-recommended users have better outcomes on average.
"""
import os
import numpy as np
import pandas as pd

np.random.seed(42)

# ============================================================
# Shared helper functions
# ============================================================

def generate_ua_features(n, organic_ratio=0.06):
    """Generate UA features for n users. ~6% are organic (all zeros)."""
    n_organic = int(n * organic_ratio)
    n_paid = n - n_organic

    data = {}
    data['trackinglink_count'] = np.random.poisson(3, n_paid).clip(1, 20)
    data['DA_count'] = np.random.poisson(1.5, n_paid).clip(0, 15)
    data['SA_count'] = np.random.poisson(0.8, n_paid).clip(0, 10)
    data['unique_channel_count'] = np.random.poisson(1.8, n_paid).clip(1, 8)
    data['channel_entropy'] = np.random.beta(2, 3, n_paid) * 2
    data['last_touch_is_da'] = np.random.binomial(1, 0.35, n_paid)
    data['latency'] = np.random.exponential(72, n_paid).clip(0.1, 720)
    data['recency'] = np.random.exponential(12, n_paid).clip(0.01, 168)
    data['recent_touch_pressure'] = np.random.exponential(0.8, n_paid).clip(0, 10)
    data['touch_per_latency_hour'] = np.random.exponential(0.15, n_paid).clip(0, 3)
    data['last1h_touch_count'] = np.random.poisson(1.2, n_paid).clip(0, 10)
    data['recent_24h_ratio'] = np.random.beta(3, 2, n_paid)
    data['click_ratio'] = np.random.beta(2, 5, n_paid)
    data['impression_count'] = np.random.poisson(8, n_paid).clip(0, 100)
    data['is_single_touch_install'] = np.random.binomial(1, 0.25, n_paid)

    paid_df = pd.DataFrame(data)
    organic_df = pd.DataFrame(0, index=range(n_organic), columns=paid_df.columns)
    organic_df['click_ratio'] = 0.0
    organic_df['channel_entropy'] = 0.0
    organic_df['recent_24h_ratio'] = 0.0

    df = pd.concat([paid_df, organic_df], ignore_index=True)
    return df.sample(frac=1, random_state=np.random.randint(10000)).reset_index(drop=True)


def generate_inapp_features(n):
    """Generate in-app M5 features."""
    data = {}
    has_view = np.random.binomial(1, 0.665, n)
    data['product_viewed_count'] = has_view * np.random.poisson(3, n).clip(0, 30)
    data['user_signin'] = np.random.binomial(1, 0.679, n)
    data['product_addedtocart'] = np.random.binomial(1, 0.118, n)
    data['deeplink_open'] = np.random.binomial(1, 0.126, n)
    data['home_viewed'] = np.random.binomial(1, 0.382, n)
    data['addtowishlist'] = np.random.binomial(1, 0.055, n)
    data['onboarding'] = np.random.binomial(1, 0.160, n)
    data['user_signup'] = np.random.binomial(1, 0.113, n)
    data['total_events'] = np.random.poisson(8, n).clip(1, 60)
    data['n_event_types'] = np.random.poisson(3, n).clip(1, 10)
    return pd.DataFrame(data)


def compute_user_trigger_affinity(ua_df, inapp_df):
    """Compute each user's affinity score for each trigger. Returns dict of arrays."""
    n = len(ua_df)
    affinities = {}

    rtp = ua_df['recent_touch_pressure'].values
    ce = ua_df['channel_entropy'].values
    pv = inapp_df['product_viewed_count'].values
    signin = inapp_df['user_signin'].values
    cart = inapp_df['product_addedtocart'].values
    recent = ua_df['recent_24h_ratio'].values

    # Each trigger appeals to different user profiles
    affinities['price_appeal'] = 0.12 * np.minimum(rtp / 3, 1) + 0.05 * cart + 0.03 * (1 - signin)
    affinities['social_proof'] = 0.10 * np.minimum(ce / 1.5, 1) + 0.06 * signin + 0.02 * (pv > 0).astype(float)
    affinities['scarcity'] = 0.08 * recent + 0.04 * (pv > 2).astype(float) + 0.03 * np.minimum(rtp / 2, 1)
    affinities['novelty'] = 0.09 * np.minimum(pv / 5, 1) + 0.03 * (1 - cart) + 0.02 * np.minimum(ce / 1.0, 1)

    return affinities


def generate_trigger_outcomes(ua_df, inapp_df, triggers, base_click=0.15):
    """Generate modal_clicked and first_session_purchase with heterogeneous effects."""
    n = len(ua_df)
    affinities = compute_user_trigger_affinity(ua_df, inapp_df)

    click_prob = np.full(n, base_click)
    for i in range(n):
        t = triggers.iloc[i] if hasattr(triggers, 'iloc') else triggers[i]
        if t in affinities:
            click_prob[i] += affinities[t][i]

    click_prob = np.clip(click_prob + np.random.normal(0, 0.03, n), 0.02, 0.95)
    modal_clicked = np.random.binomial(1, click_prob)

    # First session purchase
    purchase_prob = (
        0.05
        + 0.08 * modal_clicked
        + 0.02 * np.minimum(inapp_df['product_viewed_count'].values / 5, 1)
        + 0.03 * inapp_df['product_addedtocart'].values
    )
    purchase_prob = np.clip(purchase_prob + np.random.normal(0, 0.02, n), 0.01, 0.5)
    first_session_purchase = np.random.binomial(1, purchase_prob)

    return modal_clicked, first_session_purchase


def generate_outcomes(ua_df, inapp_df, purchase_rate=0.23, churn_rate=0.34):
    """Generate d3_purchase and d3_churn correlated with features."""
    n = len(ua_df)

    logit_purchase = (
        -2.0
        + 0.15 * inapp_df['product_viewed_count']
        + 0.8 * inapp_df['user_signin']
        + 1.5 * inapp_df['product_addedtocart']
        + 0.3 * inapp_df['deeplink_open']
        + 0.05 * ua_df['trackinglink_count']
        + 0.02 * ua_df['recent_touch_pressure']
        - 0.5 * inapp_df['onboarding']
        + np.random.normal(0, 0.5, n)
    )
    purchase_prob = 1 / (1 + np.exp(-logit_purchase))
    threshold = np.quantile(purchase_prob, 1 - purchase_rate)
    d3_purchase = (purchase_prob >= threshold).astype(int)

    logit_churn = (
        0.5
        - 0.2 * inapp_df['product_viewed_count']
        - 0.6 * inapp_df['user_signin']
        - 0.3 * inapp_df['home_viewed']
        - 0.1 * ua_df['trackinglink_count']
        + 0.3 * (inapp_df['total_events'] < 3).astype(int)
        + np.random.normal(0, 0.5, n)
    )
    churn_prob = 1 / (1 + np.exp(-logit_churn))
    threshold_c = np.quantile(churn_prob, 1 - churn_rate)
    d3_churn = (churn_prob >= threshold_c).astype(int)

    # Can't both purchase and churn
    d3_churn = d3_churn * (1 - d3_purchase)

    return d3_purchase, d3_churn


# ============================================================
# Generate weekly_YYYY-MM-DD.csv (1000 users)
# ============================================================
from datetime import datetime

APP_NAME = "ablog"
os.makedirs(f'/Users/ab180/Desktop/David/airbridge-entry-api-prototype/data/{APP_NAME}', exist_ok=True)

today_str = datetime.now().strftime('%Y-%m-%d')
print("=" * 60)
print(f"Generating weekly_{today_str}.csv (1000 users)...")
print("=" * 60)

n_weekly = 1000
ua_w = generate_ua_features(n_weekly)
inapp_w = generate_inapp_features(n_weekly)

TRIGGERS = ['price_appeal', 'social_proof', 'scarcity', 'novelty']

# 20% random assignment, 80% model-recommended
is_random = np.random.binomial(1, 0.2, n_weekly)

# For random users: uniformly random trigger
random_triggers = np.random.choice(TRIGGERS, n_weekly)

# For model-recommended users: pick the trigger with highest affinity
affinities = compute_user_trigger_affinity(ua_w, inapp_w)
affinity_matrix = np.column_stack([affinities[t] for t in TRIGGERS])
best_trigger_idx = affinity_matrix.argmax(axis=1)
model_triggers = np.array([TRIGGERS[i] for i in best_trigger_idx])

# Combine: random users get random trigger, model users get best trigger
assigned_trigger = np.where(is_random == 1, random_triggers, model_triggers)

# Generate outcomes
modal_clicked, first_session_purchase = generate_trigger_outcomes(
    ua_w, inapp_w, pd.Series(assigned_trigger)
)
d3_purchase, d3_churn = generate_outcomes(ua_w, inapp_w)

# Assemble DataFrame
weekly_df = pd.concat([
    pd.DataFrame({
        'app_id': 'ablog',
        'user_id': [f'w_{i:04d}' for i in range(n_weekly)],
    }),
    ua_w.reset_index(drop=True),
    inapp_w.reset_index(drop=True),
    pd.DataFrame({
        'assigned_trigger': assigned_trigger,
        'is_random': is_random,
        'modal_clicked': modal_clicked,
        'first_session_purchase': first_session_purchase,
        'd3_purchase': d3_purchase,
        'd3_churn': d3_churn,
    }),
], axis=1)

weekly_df.to_csv(f'/Users/ab180/Desktop/David/airbridge-entry-api-prototype/data/{APP_NAME}/weekly_{today_str}.csv', index=False)

print(f"  Total users: {len(weekly_df)}")
print(f"  Random (is_random=1): {is_random.sum()} ({is_random.mean():.1%})")
print(f"  Model-recommended (is_random=0): {(1-is_random).sum()} ({(1-is_random).mean():.1%})")
print(f"  Organic (UA=0): {(ua_w['trackinglink_count'] == 0).sum()}")
print(f"  D3 purchase rate: {d3_purchase.mean():.1%}")
print(f"  D3 churn rate: {d3_churn.mean():.1%}")
print(f"\n  Trigger distribution:")
print(weekly_df['assigned_trigger'].value_counts().to_string(header=False))
print(f"\n  Click rate — Random users: {weekly_df[weekly_df['is_random']==1]['modal_clicked'].mean():.1%}")
print(f"  Click rate — Model users:  {weekly_df[weekly_df['is_random']==0]['modal_clicked'].mean():.1%}")

# ============================================================
# Generate rct_data.csv (8000 users) — Phase 1 pure RCT
# ============================================================
print()
print("=" * 60)
print("Generating rct_data.csv (8000 users)...")
print("=" * 60)

n_rct = 8000
ua_r = generate_ua_features(n_rct)
inapp_r = generate_inapp_features(n_rct)

# Phase 1: ALL users are randomly assigned (including control)
ALL_TRIGGERS_RCT = TRIGGERS + ['control']
rct_triggers = pd.Series(np.random.choice(ALL_TRIGGERS_RCT, n_rct))

modal_clicked_r, first_session_purchase_r = generate_trigger_outcomes(
    ua_r, inapp_r, rct_triggers
)
d3_purchase_r, d3_churn_r = generate_outcomes(ua_r, inapp_r)

rct_df = pd.concat([
    pd.DataFrame({
        'app_id': 'ablog',
        'user_id': [f'rct_{i:05d}' for i in range(n_rct)],
    }),
    ua_r.reset_index(drop=True),
    inapp_r.reset_index(drop=True),
    pd.DataFrame({
        'assigned_trigger': rct_triggers.values,
        'modal_clicked': modal_clicked_r,
        'first_session_purchase': first_session_purchase_r,
        'd3_purchase': d3_purchase_r,
        'd3_churn': d3_churn_r,
    }),
], axis=1)

rct_df.to_csv(f'/Users/ab180/Desktop/David/airbridge-entry-api-prototype/data/{APP_NAME}/rct_data.csv', index=False)

print(f"  Total users: {len(rct_df)}")
print(f"  Trigger distribution:")
print(rct_df['assigned_trigger'].value_counts().to_string(header=False))
print(f"\n  Click rate by trigger:")
for t in ALL_TRIGGERS_RCT:
    mask = rct_df['assigned_trigger'] == t
    print(f"    {t}: {rct_df.loc[mask, 'modal_clicked'].mean():.1%}")
print(f"\n  D3 purchase rate: {d3_purchase_r.mean():.1%}")
print(f"  D3 churn rate: {d3_churn_r.mean():.1%}")

print("\nDone!")
