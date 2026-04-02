"""
UA Feature Deep Analysis for Athler Dataset
Goal: Identify which UA features to keep vs. drop for experiment/modeling
"""
import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

OUT = '/Users/ab180/Desktop/David/Research/athler'
df = pd.read_parquet(f'{OUT}/athler_v1.parquet')
clean = df[df['IS_HAS_FRAUD'] != 1].copy()
N = len(clean)

print(f"Dataset: {N:,} clean users (fraud excluded from {len(df):,} total)")
print()

# ============================================================
# 1. ALL COLUMNS
# ============================================================
print("=" * 80)
print("1. ALL COLUMNS IN DATASET")
print("=" * 80)
for i, c in enumerate(df.columns):
    print(f"  [{i:3d}] {c}  (dtype: {df[c].dtype})")
print(f"\nTotal columns: {len(df.columns)}")

# ============================================================
# 2. UA FEATURE DEFINITIONS (from run_analysis.py)
# ============================================================
ua_cols = ['has_touchpoint', 'has_last_touch', 'last_touch_is_trackinglink',
           'last_touch_is_da', 'last_touch_is_sa', 'has_term',
           'is_single_touch_install', 'last_is_click', 'last_is_impression',
           'first_is_click', 'first_is_impression',
           'latency', 'touch_window', 'touch_per_window_hour', 'recency',
           'recent_touch_pressure', 'recent_24h_ratio', 'recent_24h_multiple',
           'DA_count', 'SA_count', 'total_touch_count', 'trackinglink_count',
           'unique_channel_count', 'channel_entropy', 'term_total_count', 'term_unique_count',
           'last30min_touch_count', 'last1h_touch_count', 'last3h_touch_count',
           'last12h_touch_count', 'last24h_touch_count',
           'touch_per_latency_day', 'touch_per_latency_hour',
           'click_count', 'impression_count', 'click_ratio',
           'kw_brand_search', 'kw_product_search', 'kw_promo_season_search']

device_cols = ['OS_NAME', 'DEVICE_MANUFACTURER', 'DEVICE_LANGUAGE', 'DEVICE_TIMEZONE',
               'is_installed_06_10', 'is_installed_10_14', 'is_installed_14_18',
               'is_installed_18_22', 'is_installed_22_02', 'is_installed_02_06']

# ============================================================
# 3. IDENTIFY CREATIVE-RELATED COLUMNS
# ============================================================
print("\n" + "=" * 80)
print("2. CREATIVE-RELATED COLUMNS (candidates for exclusion)")
print("=" * 80)
creative_keywords = ['creative', 'ad_', 'campaign', 'adgroup', 'ad_group', 'content', 'material']
all_cols = list(df.columns)
creative_cols = [c for c in all_cols if any(kw in c.lower() for kw in creative_keywords)]
print(f"Found {len(creative_cols)} creative-related columns:")
for c in creative_cols:
    non_null = clean[c].notna().mean()
    print(f"  {c}  (non-null: {non_null:.1%}, dtype: {clean[c].dtype})")

# Also check for any columns with 'term' or 'keyword' that might be creative-adjacent
kw_cols = [c for c in all_cols if any(kw in c.lower() for kw in ['term', 'keyword', 'kw_'])]
print(f"\nKeyword/term columns (may encode creative intent):")
for c in kw_cols:
    if c in clean.columns:
        non_null = clean[c].notna().mean()
        if clean[c].dtype in ['float64', 'int64']:
            print(f"  {c}  (non-null: {non_null:.1%}, mean: {clean[c].mean():.4f}, non-zero: {(clean[c]!=0).mean():.1%})")
        else:
            print(f"  {c}  (non-null: {non_null:.1%}, dtype: {clean[c].dtype})")

# ============================================================
# 4. UA FEATURE BASIC STATS
# ============================================================
print("\n" + "=" * 80)
print("3. UA FEATURE BASIC STATS")
print("=" * 80)

stats_rows = []
for c in ua_cols:
    if c not in clean.columns:
        print(f"  WARNING: {c} not found in data!")
        continue
    s = clean[c]
    row = {
        'feature': c,
        'dtype': str(s.dtype),
        'null_pct': s.isna().mean(),
        'non_zero_pct': (s != 0).mean() if s.dtype in ['float64', 'int64'] else np.nan,
        'mean': s.mean() if s.dtype in ['float64', 'int64'] else np.nan,
        'std': s.std() if s.dtype in ['float64', 'int64'] else np.nan,
        'min': s.min() if s.dtype in ['float64', 'int64'] else np.nan,
        'p25': s.quantile(0.25) if s.dtype in ['float64', 'int64'] else np.nan,
        'median': s.median() if s.dtype in ['float64', 'int64'] else np.nan,
        'p75': s.quantile(0.75) if s.dtype in ['float64', 'int64'] else np.nan,
        'p95': s.quantile(0.95) if s.dtype in ['float64', 'int64'] else np.nan,
        'max': s.max() if s.dtype in ['float64', 'int64'] else np.nan,
    }
    stats_rows.append(row)

stats_df = pd.DataFrame(stats_rows)
# Print nicely
for _, r in stats_df.iterrows():
    print(f"\n  {r['feature']}")
    print(f"    null: {r['null_pct']:.1%} | non-zero: {r['non_zero_pct']:.1%}")
    print(f"    mean: {r['mean']:.4f} | std: {r['std']:.4f}")
    print(f"    min: {r['min']:.4f} | p25: {r['p25']:.4f} | median: {r['median']:.4f} | p75: {r['p75']:.4f} | p95: {r['p95']:.4f} | max: {r['max']:.4f}")

# ============================================================
# 5. LOW VARIANCE FEATURES
# ============================================================
print("\n" + "=" * 80)
print("4. LOW VARIANCE / MOSTLY-ZERO FEATURES")
print("=" * 80)
print("\nFeatures where >90% of values are zero:")
for _, r in stats_df.iterrows():
    if r['non_zero_pct'] < 0.10:
        print(f"  {r['feature']:40s}  non-zero: {r['non_zero_pct']:.1%}  (mean={r['mean']:.6f})")

print("\nFeatures where >80% of values are zero:")
for _, r in stats_df.iterrows():
    if 0.10 <= r['non_zero_pct'] < 0.20:
        print(f"  {r['feature']:40s}  non-zero: {r['non_zero_pct']:.1%}  (mean={r['mean']:.6f})")

# ============================================================
# 6. BINARY FEATURES ANALYSIS
# ============================================================
print("\n" + "=" * 80)
print("5. BINARY FEATURE ANALYSIS")
print("=" * 80)
binary_cols = [c for c in ua_cols if c in clean.columns and
               set(clean[c].dropna().unique()).issubset({0, 1, 0.0, 1.0})]
print(f"\nBinary UA features ({len(binary_cols)}):")
for c in binary_cols:
    rate = clean[c].mean()
    print(f"  {c:40s}  rate={rate:.1%}  (N=1: {int(clean[c].sum()):,})")

# ============================================================
# 7. CORRELATION ANALYSIS
# ============================================================
print("\n" + "=" * 80)
print("6. CORRELATION ANALYSIS (UA features)")
print("=" * 80)

numeric_ua = [c for c in ua_cols if c in clean.columns and clean[c].dtype in ['float64', 'int64']]
corr = clean[numeric_ua].corr()

# Find highly correlated pairs
print("\nHighly correlated pairs (|r| > 0.8):")
high_corr_pairs = []
for i in range(len(numeric_ua)):
    for j in range(i+1, len(numeric_ua)):
        r = corr.iloc[i, j]
        if abs(r) > 0.8:
            high_corr_pairs.append((numeric_ua[i], numeric_ua[j], r))

high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
for f1, f2, r in high_corr_pairs:
    print(f"  {r:+.3f}  {f1} <-> {f2}")

print(f"\nModerately correlated pairs (0.6 < |r| <= 0.8):")
mod_corr_pairs = []
for i in range(len(numeric_ua)):
    for j in range(i+1, len(numeric_ua)):
        r = corr.iloc[i, j]
        if 0.6 < abs(r) <= 0.8:
            mod_corr_pairs.append((numeric_ua[i], numeric_ua[j], r))
mod_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
for f1, f2, r in mod_corr_pairs:
    print(f"  {r:+.3f}  {f1} <-> {f2}")

# ============================================================
# 8. ORGANIC vs PAID FEATURE AVAILABILITY
# ============================================================
print("\n" + "=" * 80)
print("7. ORGANIC vs PAID: FEATURE AVAILABILITY")
print("=" * 80)
clean['is_paid'] = clean['has_touchpoint'] == 1
paid = clean[clean['is_paid']]
organic = clean[~clean['is_paid']]
print(f"Paid users: {len(paid):,} ({len(paid)/N:.1%})")
print(f"Organic users: {len(organic):,} ({len(organic)/N:.1%})")

print(f"\n{'Feature':40s}  {'Paid non-zero':>14s}  {'Organic non-zero':>16s}  {'Paid-only?':>10s}")
print("-" * 85)
for c in numeric_ua:
    paid_nz = (paid[c] != 0).mean()
    org_nz = (organic[c] != 0).mean()
    paid_only = "YES" if org_nz < 0.01 and paid_nz > 0.05 else ""
    print(f"  {c:38s}  {paid_nz:>12.1%}  {org_nz:>14.1%}  {paid_only:>10s}")

# ============================================================
# 9. FEATURE IMPORTANCE (from existing model)
# ============================================================
print("\n" + "=" * 80)
print("8. FEATURE IMPORTANCE (RF trained on device+UA → D7 purchase)")
print("=" * 80)

# Load existing results if available
try:
    with open(f'{OUT}/analysis_results.json', 'r') as f:
        existing_results = json.load(f)
    if 'feature_importance' in existing_results:
        fi = existing_results['feature_importance']
        print(f"\nFrom cached results:")
        print(f"  Device importance: {fi.get('device_pct', 'N/A')}")
        print(f"  UA importance: {fi.get('ua_pct', 'N/A')}")
        if 'top_features' in fi:
            print(f"\n  Top features:")
            for feat, imp in fi['top_features'].items():
                print(f"    {feat:40s}  {imp:.4f}")
except Exception as e:
    print(f"Could not load cached results: {e}")

# Quick RF to get feature importance
print("\nTraining quick RF for feature importance...")
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def prepare_features(data, cols):
    X = data[cols].copy()
    cat_cols = X.select_dtypes(include=['object']).columns
    if len(cat_cols) > 0:
        X = pd.get_dummies(X, columns=cat_cols, drop_first=False)
    return X.fillna(0).astype(float)

X_ua = prepare_features(clean, ua_cols)
y = clean['IS_D7_PURCHASE'].values

rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_ua, y)
fi = pd.Series(rf.feature_importances_, index=X_ua.columns).sort_values(ascending=False)

print(f"\nUA-only Feature Importance (top 20):")
for feat, imp in fi.head(20).items():
    print(f"  {feat:40s}  {imp:.4f}  ({imp/fi.sum():.1%})")

print(f"\nUA-only Feature Importance (bottom 10):")
for feat, imp in fi.tail(10).items():
    print(f"  {feat:40s}  {imp:.4f}  ({imp/fi.sum():.1%})")

# ============================================================
# 10. SUMMARY & RECOMMENDATIONS
# ============================================================
print("\n" + "=" * 80)
print("9. SUMMARY & RECOMMENDATIONS")
print("=" * 80)

# Classify features
print("\n--- FEATURE CLASSIFICATION ---")

# Group 1: Temporal/recency features
temporal = ['latency', 'recency', 'recent_touch_pressure', 'recent_24h_ratio',
            'recent_24h_multiple', 'touch_window', 'touch_per_window_hour',
            'touch_per_latency_day', 'touch_per_latency_hour',
            'last30min_touch_count', 'last1h_touch_count', 'last3h_touch_count',
            'last12h_touch_count', 'last24h_touch_count']

# Group 2: Channel/source features
channel = ['has_touchpoint', 'has_last_touch', 'last_touch_is_trackinglink',
           'last_touch_is_da', 'last_touch_is_sa',
           'DA_count', 'SA_count', 'total_touch_count', 'trackinglink_count',
           'unique_channel_count', 'channel_entropy']

# Group 3: Interaction type
interaction = ['is_single_touch_install', 'last_is_click', 'last_is_impression',
               'first_is_click', 'first_is_impression',
               'click_count', 'impression_count', 'click_ratio']

# Group 4: Keyword/term (creative-adjacent)
keyword = ['has_term', 'term_total_count', 'term_unique_count',
           'kw_brand_search', 'kw_product_search', 'kw_promo_season_search']

print("\n[A] TEMPORAL/RECENCY FEATURES:")
for c in temporal:
    imp_val = fi.get(c, 0)
    nz = (clean[c] != 0).mean() if c in clean.columns else 0
    print(f"  {c:40s}  importance={imp_val:.4f}  non-zero={nz:.1%}")

print("\n[B] CHANNEL/SOURCE FEATURES:")
for c in channel:
    imp_val = fi.get(c, 0)
    nz = (clean[c] != 0).mean() if c in clean.columns else 0
    print(f"  {c:40s}  importance={imp_val:.4f}  non-zero={nz:.1%}")

print("\n[C] INTERACTION TYPE FEATURES:")
for c in interaction:
    imp_val = fi.get(c, 0)
    nz = (clean[c] != 0).mean() if c in clean.columns else 0
    print(f"  {c:40s}  importance={imp_val:.4f}  non-zero={nz:.1%}")

print("\n[D] KEYWORD/TERM FEATURES (creative-adjacent, consider excluding):")
for c in keyword:
    imp_val = fi.get(c, 0)
    nz = (clean[c] != 0).mean() if c in clean.columns else 0
    print(f"  {c:40s}  importance={imp_val:.4f}  non-zero={nz:.1%}")

# Redundancy groups
print("\n--- REDUNDANCY GROUPS (highly correlated, pick one from each) ---")
for f1, f2, r in high_corr_pairs:
    imp1 = fi.get(f1, 0)
    imp2 = fi.get(f2, 0)
    keep = f1 if imp1 >= imp2 else f2
    drop = f2 if imp1 >= imp2 else f1
    print(f"  {f1} <-> {f2}  (r={r:+.3f})  → KEEP {keep}, DROP {drop}")

# Low-value features
print("\n--- LOW-VALUE FEATURES (low importance AND mostly zero) ---")
for _, r in stats_df.iterrows():
    c = r['feature']
    imp_val = fi.get(c, 0)
    if r['non_zero_pct'] < 0.15 and imp_val < 0.02:
        print(f"  {c:40s}  importance={imp_val:.4f}  non-zero={r['non_zero_pct']:.1%}  → DROP candidate")

print("\n\nDone.")
