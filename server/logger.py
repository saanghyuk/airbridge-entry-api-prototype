"""
Prediction Logger — Supabase

모든 API 예측 결과를 Supabase에 기록합니다.
이 데이터가 나중에 CATE 모델 학습에 사용됩니다.

핵심 필드:
- is_random: True면 CATE 학습에 사용 가능 (랜덤 배정)
- best_trigger: 이 유저에게 배정된 trigger
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional

# Supabase connection (via environment variables)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client = None


def _get_client():
    global _client
    if _client is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("[Logger] Supabase connected")
        except Exception as e:
            print(f"[Logger] Supabase connection failed: {e}")
            print("[Logger] Prediction logging disabled — set SUPABASE_URL and SUPABASE_KEY env vars")
    return _client


def log_prediction(app_id: str, prediction: dict):
    """
    예측 결과를 Supabase에 기록.
    Supabase 미설정 시 조용히 스킵 (서비스에 영향 없음).
    """
    client = _get_client()
    if client is None:
        return  # Supabase not configured — skip logging

    try:
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "app_id": app_id,
            "user_id": prediction["user_id"],
            "best_trigger": prediction["best_trigger"],
            "is_random": prediction["is_random"],
            "trigger_scores": json.dumps(prediction["trigger_scores"]) if prediction["trigger_scores"] else None,
            "d3_purchase_prob": prediction["d3_purchase_prob"],
            "d3_churn_prob": prediction["d3_churn_prob"],
        }
        client.table("prediction_logs").insert(row).execute()
    except Exception as e:
        # Logging failure must never crash the service
        print(f"[Logger] Failed to log: {e}")
