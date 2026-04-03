"""
모든 앱의 모델을 한번에 학습하고 업로드하는 스크립트.

사용법:
    python scripts/train_all_apps.py

앱 목록은 configs/ 폴더의 json 파일에서 자동 감지합니다.
데이터는 data/{app_name}/weekly_YYYY-MM-DD.csv 에서 최신 파일을 자동으로 찾습니다.
"""
import os
import glob
import json
import pickle
import requests
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

# 설정
SERVER_URL = "https://airbridge-entry-api-prototype.onrender.com"
CONFIGS_DIR = "configs"
DATA_DIR = "data"
MODELS_DIR = "models"

UA_FEATURES = [
    'trackinglink_count', 'DA_count', 'SA_count',
    'unique_channel_count', 'channel_entropy', 'last_touch_is_da',
    'latency', 'recency', 'recent_touch_pressure',
    'touch_per_latency_hour', 'last1h_touch_count', 'recent_24h_ratio',
    'click_ratio', 'impression_count', 'is_single_touch_install'
]
INAPP_FEATURES = [
    'product_viewed_count', 'user_signin', 'product_addedtocart',
    'deeplink_open', 'home_viewed', 'addtowishlist',
    'onboarding', 'user_signup', 'total_events', 'n_event_types'
]
ALL_FEATURES = UA_FEATURES + INAPP_FEATURES
TRIGGERS = ['price_appeal', 'social_proof', 'scarcity', 'novelty']

def train_app(app_id):
    """한 앱의 모델을 학습하고 업로드"""
    print(f"\n{'='*50}")
    print(f"[{app_id}] 학습 시작")
    print(f"{'='*50}")

    # Find latest weekly data for this app
    data_dir = os.path.join(DATA_DIR, app_id)
    weekly_files = sorted(glob.glob(os.path.join(data_dir, "weekly_*.csv")))
    if not weekly_files:
        print(f"  ⚠️ 데이터 없음 — 건너뜀")
        return
    latest_file = weekly_files[-1]
    df = pd.read_csv(latest_file)
    print(f"  📂 {os.path.basename(latest_file)} 로드 (파일 {len(weekly_files)}개 중 최신)")
    if 'app_id' in df.columns:
        df = df[df['app_id'] == app_id].reset_index(drop=True)

    if len(df) == 0:
        print(f"  ⚠️ 데이터 없음 — 건너뜀")
        return

    print(f"  유저: {len(df)}명")

    # 모델 저장 디렉토리
    model_dir = os.path.join(MODELS_DIR, app_id)
    os.makedirs(model_dir, exist_ok=True)

    X = df[ALL_FEATURES].values

    # D3 Purchase
    y_purchase = df['d3_purchase'].values
    purchase_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    purchase_model.fit(X, y_purchase)
    auc_p = cross_val_score(purchase_model, X, y_purchase, cv=min(5, len(df)), scoring='roc_auc').mean()
    print(f"  D3 Purchase AUC: {auc_p:.3f}")

    with open(os.path.join(model_dir, "d3_purchase_model.pkl"), "wb") as f:
        pickle.dump({"model": purchase_model, "feature_names": ALL_FEATURES}, f)

    # D3 Churn
    y_churn = df['d3_churn'].values
    churn_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    churn_model.fit(X, y_churn)
    auc_c = cross_val_score(churn_model, X, y_churn, cv=min(5, len(df)), scoring='roc_auc').mean()
    print(f"  D3 Churn AUC: {auc_c:.3f}")

    with open(os.path.join(model_dir, "d3_churn_model.pkl"), "wb") as f:
        pickle.dump({"model": churn_model, "feature_names": ALL_FEATURES}, f)

    # CATE (랜덤 유저만)
    if 'is_random' in df.columns:
        df_cate = df[df['is_random'] == 1]
        if len(df_cate) >= 50 and 'modal_clicked' in df.columns:
            X_rows, y_rows = [], []
            for _, row in df_cate.iterrows():
                features = row[ALL_FEATURES].values
                trigger = row['assigned_trigger']
                if trigger not in TRIGGERS:
                    continue
                trigger_onehot = [1 if t == trigger else 0 for t in TRIGGERS]
                X_rows.append(np.concatenate([features, trigger_onehot]))
                y_rows.append(row['modal_clicked'])

            if len(X_rows) >= 50:
                cate_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
                cate_model.fit(X_rows, y_rows)
                with open(os.path.join(model_dir, "cate_model.pkl"), "wb") as f:
                    pickle.dump({"model": cate_model, "treatment_triggers": TRIGGERS, "feature_names": ALL_FEATURES}, f)
                print(f"  CATE: 랜덤 유저 {len(X_rows)}명으로 학습")
            else:
                print(f"  CATE: 랜덤 유저 {len(X_rows)}명 — 부족하여 건너뜀")
        else:
            print(f"  CATE: 데이터 부족 또는 modal_clicked 없음 — 건너뜀")

    # 서버 업로드
    for fname in ["d3_purchase_model.pkl", "d3_churn_model.pkl", "cate_model.pkl"]:
        fpath = os.path.join(model_dir, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "rb") as f:
                resp = requests.post(f"{SERVER_URL}/v1/models/{app_id}/upload", files={"file": (fname, f)})
            if resp.status_code == 200:
                print(f"  ↑ {fname} → {resp.json().get('mode', 'ok')}")
            else:
                print(f"  ✗ {fname} 업로드 실패: {resp.status_code}")
        except requests.ConnectionError:
            print(f"  ✗ 서버 연결 실패")
            break

def main():
    # configs/ 폴더에서 앱 목록 자동 감지
    app_ids = []
    for fname in sorted(os.listdir(CONFIGS_DIR)):
        if fname.endswith('.json') and fname != 'default_commerce.json':
            app_id = fname.replace('.json', '')
            app_ids.append(app_id)

    if not app_ids:
        print("configs/ 폴더에 앱 config가 없습니다. onboarding.ipynb를 먼저 실행하세요.")
        return

    print(f"학습할 앱: {app_ids}")

    for app_id in app_ids:
        train_app(app_id)

    print(f"\n{'='*50}")
    print(f"완료! {len(app_ids)}개 앱 학습 + 업로드")

if __name__ == "__main__":
    main()
