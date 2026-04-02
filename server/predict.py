"""
Airbridge Entry API — Server Inference Module

서버에서 실행되는 inference 코드. 학습 로직 없이 파라미터 파일만 로드하여 예측.
앱별로 모델 디렉토리가 분리되어 있고, 최초 요청 시 lazy loading.

파일 구조:
  models/{app_id}/fa_params.json        — FA loading matrix + standardization params
  models/{app_id}/d3_purchase_model.pkl — D3 purchase prediction model
  models/{app_id}/d3_churn_model.pkl    — D3 churn prediction model
  models/{app_id}/cate_model.pkl        — Trigger CATE model (없으면 exploration mode)
"""
import json
import pickle
import random
import numpy as np
from pathlib import Path
from typing import Optional

MODEL_DIR = Path(__file__).parent.parent / "models"

# Trigger options
TREATMENT_TRIGGERS = ["price_appeal", "social_proof", "scarcity", "novelty"]
ALL_TRIGGERS = TREATMENT_TRIGGERS + ["control"]

# Feature column order (must match feature_store.py)
UA_FEATURE_NAMES = [
    'trackinglink_count', 'DA_count', 'SA_count', 'unique_channel_count',
    'channel_entropy', 'last_touch_is_da', 'latency', 'recency',
    'recent_touch_pressure', 'touch_per_latency_hour', 'last1h_touch_count',
    'recent_24h_ratio', 'click_ratio', 'impression_count', 'is_single_touch_install',
]

# 앱별 모델 캐시: app_id -> models dict
_model_cache: dict[str, dict] = {}


def load_models_for_app(app_id: str, model_dir: Path = MODEL_DIR) -> Optional[dict]:
    """
    특정 앱의 모델을 로드. 이미 로드된 경우 캐시에서 반환.

    Args:
        app_id: 앱 식별자 (e.g., "ablog", "sample_app")
        model_dir: 모델 루트 디렉토리

    Returns:
        모델 dict (fa, pltv, churn, cate) 또는 앱이 없으면 None
    """
    if app_id in _model_cache:
        return _model_cache[app_id]

    app_dir = model_dir / app_id
    if not app_dir.exists():
        return None  # Unknown app

    # 필수 파일 체크 (2개 다 있어야 로드)
    required = ["d3_purchase_model.pkl", "d3_churn_model.pkl"]
    missing = [f for f in required if not (app_dir / f).exists()]
    if missing:
        print(f"[Server] [{app_id}] Missing required files: {missing} — skipping load")
        return None

    models = {}

    # FA params (optional — 연구/분석용)
    fa_path = app_dir / "fa_params.json"
    if fa_path.exists():
        with open(fa_path) as f:
            fa = json.load(f)
        models["fa"] = {
            "loading_matrix": np.array(fa["loading_matrix"]),
            "mean": np.array(fa["mean"]),
            "std": np.array(fa["std"]),
            "factor_names": fa["factor_names"],
        }
    else:
        models["fa"] = None

    # D3 Purchase model
    with open(app_dir / "d3_purchase_model.pkl", "rb") as f:
        models["pltv"] = pickle.load(f)

    # D3 Churn model
    with open(app_dir / "d3_churn_model.pkl", "rb") as f:
        models["churn"] = pickle.load(f)

    # CATE model (optional — 없으면 exploration mode)
    cate_path = app_dir / "cate_model.pkl"
    if cate_path.exists():
        with open(cate_path, "rb") as f:
            models["cate"] = pickle.load(f)
        print(f"[Server] [{app_id}] CATE model loaded -> optimized mode")
    else:
        models["cate"] = None
        print(f"[Server] [{app_id}] No CATE model -> exploration mode (random trigger)")

    _model_cache[app_id] = models
    print(f"[Server] [{app_id}] All models loaded from {app_dir}")
    return models


def reload_models_for_app(app_id: str, model_dir: Path = MODEL_DIR) -> Optional[dict]:
    """앱의 모델을 강제 리로드 (캐시 무시). pkl 업로드 후 호출."""
    if app_id in _model_cache:
        del _model_cache[app_id]
    return load_models_for_app(app_id, model_dir)


def get_loaded_apps() -> dict[str, str]:
    """현재 캐시에 로드된 앱 목록과 모드 반환."""
    result = {}
    for app_id, models in _model_cache.items():
        mode = "optimized" if models.get("cate") else "exploration"
        result[app_id] = mode
    return result


def list_available_apps(model_dir: Path = MODEL_DIR) -> list[str]:
    """models/ 디렉토리에서 사용 가능한 앱 목록 반환."""
    if not model_dir.exists():
        return []
    return [
        d.name for d in sorted(model_dir.iterdir())
        if d.is_dir() and (d / "d3_purchase_model.pkl").exists()
    ]


def predict(user_id: str, features: np.ndarray, models: dict) -> dict:
    """
    Main prediction function. Called for each API request.

    Args:
        user_id: airbridge_uuid
        features: np.ndarray of shape (25,) — 15 UA + 10 in-app features
                  (returned by FeatureStore.lookup)
        models: Loaded model dict from load_models_for_app()

    Returns:
        Clean API response dict (no mode, no latent_dimensions)
    """
    pltv = models["pltv"]
    churn = models["churn"]
    cate = models["cate"]

    # --- 1. Trigger Assignment ---
    if cate is None:
        # Exploration mode — 100% random
        trigger_scores = None
        best_trigger = random.choice(ALL_TRIGGERS)
    else:
        # Optimized mode
        feature_names = cate["feature_names"]
        # Build feature vector for CATE model using feature names
        feature_dict = dict(zip(
            UA_FEATURE_NAMES + [
                'product_viewed_count', 'user_signin', 'product_addedtocart',
                'deeplink_open', 'home_viewed', 'addtowishlist', 'onboarding',
                'user_signup', 'total_events', 'n_event_types',
            ],
            features
        ))
        x_cate = np.array([[feature_dict.get(f, 0) for f in feature_names]])

        # Predict click probability for each trigger
        trigger_scores = {}
        for trigger in cate["treatment_triggers"]:
            prob = cate["trigger_models"][trigger].predict_proba(x_cate)[0, 1]
            trigger_scores[trigger] = round(float(prob), 4)

        # 80% model recommendation, 20% random (for continued data collection)
        if random.random() < 0.2:
            best_trigger = random.choice(TREATMENT_TRIGGERS)
        else:
            best_trigger = max(trigger_scores, key=trigger_scores.get)

    # --- 3. pLTV: Purchase & Churn Prediction ---
    x_all = features.reshape(1, -1)
    d3_purchase_prob = float(pltv["model"].predict_proba(x_all)[0, 1])
    d3_churn_prob = float(churn["model"].predict_proba(x_all)[0, 1])

    # --- 4. Build Response (clean — no mode, no latent_dimensions) ---
    return {
        "user_id": user_id,
        "best_trigger": best_trigger,
        "trigger_scores": trigger_scores,
        "d3_purchase_prob": round(d3_purchase_prob, 4),
        "d3_churn_prob": round(d3_churn_prob, 4),
    }


# --- Example usage ---
if __name__ == "__main__":
    from server.feature_store import FeatureStore

    print("Loading feature store...")
    store = FeatureStore()

    # Test ablog (has CATE -> optimized mode)
    print("\n--- ablog (optimized mode) ---")
    models = load_models_for_app("ablog")
    uuids = store.list_users("ablog")
    features = store.lookup("ablog", uuids[0])
    response = predict(uuids[0], features, models)
    print(json.dumps(response, indent=2, ensure_ascii=False))

    # Test sample_app (no CATE -> exploration mode)
    print("\n--- sample_app (exploration mode) ---")
    models_sample = load_models_for_app("sample_app")
    uuids_sample = store.list_users("sample_app")
    if uuids_sample:
        features_sample = store.lookup("sample_app", uuids_sample[0])
        response_sample = predict(uuids_sample[0], features_sample, models_sample)
        print(json.dumps(response_sample, indent=2, ensure_ascii=False))
