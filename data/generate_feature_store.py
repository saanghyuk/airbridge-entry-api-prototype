"""
Generate feature_store.csv — 멀티앱 Feature Store prototype.

앱별로 유저를 생성:
  - ablog: 500 users
  - sample_app: 200 users

Simulates what Airbridge DB would provide in production:
  app_id + airbridge_uuid + 15 UA features + 10 in-app features
"""
import uuid
import numpy as np
import pandas as pd

np.random.seed(2026)

# --- Feature generation helpers ---

ua_cols = [
    'trackinglink_count', 'DA_count', 'SA_count', 'unique_channel_count',
    'channel_entropy', 'last_touch_is_da', 'latency', 'recency',
    'recent_touch_pressure', 'touch_per_latency_hour', 'last1h_touch_count',
    'recent_24h_ratio', 'click_ratio', 'impression_count', 'is_single_touch_install'
]

inapp_cols = [
    'product_viewed_count', 'user_signin', 'product_addedtocart',
    'deeplink_open', 'home_viewed', 'addtowishlist', 'onboarding',
    'user_signup', 'total_events', 'n_event_types',
]


def generate_users(app_id: str, n: int, organic_ratio: float = 0.06) -> pd.DataFrame:
    """Generate n users for a given app_id."""
    n_organic = int(n * organic_ratio)
    n_paid = n - n_organic

    paid = {
        'trackinglink_count': np.random.poisson(3, n_paid).clip(1, 20),
        'DA_count': np.random.poisson(1.5, n_paid).clip(0, 15),
        'SA_count': np.random.poisson(0.8, n_paid).clip(0, 10),
        'unique_channel_count': np.random.poisson(1.8, n_paid).clip(1, 8),
        'channel_entropy': np.random.beta(2, 3, n_paid) * 2,
        'last_touch_is_da': np.random.binomial(1, 0.35, n_paid),
        'latency': np.random.exponential(72, n_paid).clip(0.1, 720),
        'recency': np.random.exponential(12, n_paid).clip(0.01, 168),
        'recent_touch_pressure': np.random.exponential(0.8, n_paid).clip(0, 10),
        'touch_per_latency_hour': np.random.exponential(0.15, n_paid).clip(0, 3),
        'last1h_touch_count': np.random.poisson(1.2, n_paid).clip(0, 10),
        'recent_24h_ratio': np.random.beta(3, 2, n_paid),
        'click_ratio': np.random.beta(2, 5, n_paid),
        'impression_count': np.random.poisson(8, n_paid).clip(0, 100),
        'is_single_touch_install': np.random.binomial(1, 0.25, n_paid),
    }
    paid_df = pd.DataFrame(paid)

    organic_df = pd.DataFrame(0, index=range(n_organic), columns=paid_df.columns)
    organic_df['click_ratio'] = 0.0
    organic_df['channel_entropy'] = 0.0
    organic_df['recent_24h_ratio'] = 0.0

    ua_df = pd.concat([paid_df, organic_df], ignore_index=True)

    # In-app features
    has_view = np.random.binomial(1, 0.665, n)
    inapp = {
        'product_viewed_count': has_view * np.random.poisson(3, n).clip(0, 30),
        'user_signin': np.random.binomial(1, 0.679, n),
        'product_addedtocart': np.random.binomial(1, 0.118, n),
        'deeplink_open': np.random.binomial(1, 0.126, n),
        'home_viewed': np.random.binomial(1, 0.382, n),
        'addtowishlist': np.random.binomial(1, 0.055, n),
        'onboarding': np.random.binomial(1, 0.160, n),
        'user_signup': np.random.binomial(1, 0.113, n),
        'total_events': np.random.poisson(8, n).clip(1, 60),
        'n_event_types': np.random.poisson(3, n).clip(1, 10),
    }
    inapp_df = pd.DataFrame(inapp)

    # Assemble
    df = pd.concat([
        pd.DataFrame({
            'app_id': app_id,
            'airbridge_uuid': [str(uuid.uuid4()) for _ in range(n)],
        }),
        ua_df.sample(frac=1, random_state=np.random.randint(10000)).reset_index(drop=True),
        inapp_df,
    ], axis=1)

    return df


# --- Generate for each app ---
ablog_df = generate_users('ablog', 500)
sample_df = generate_users('sample_app', 200)

df = pd.concat([ablog_df, sample_df], ignore_index=True)

out_path = '/Users/ab180/Desktop/David/airbridge-entry-api-prototype/data/feature_store.csv'
df.to_csv(out_path, index=False)

print(f"Generated {len(df)} users -> {out_path}")
for aid in df['app_id'].unique():
    n = (df['app_id'] == aid).sum()
    organic = ((df['app_id'] == aid) & (df['trackinglink_count'] == 0)).sum()
    print(f"  {aid}: {n} users ({organic} organic)")
print(f"  Columns: {list(df.columns)}")

print(f"\nFirst 3 UUIDs per app (for testing):")
for aid in df['app_id'].unique():
    print(f"  [{aid}]")
    for uid in df.loc[df['app_id'] == aid, 'airbridge_uuid'].head(3):
        print(f"    {uid}")
