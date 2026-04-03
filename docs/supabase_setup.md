# Supabase 설정 가이드

## 1. Supabase 프로젝트 생성
1. https://supabase.com 에서 무료 계정 생성
2. New Project 생성

## 2. 테이블 생성

SQL Editor에서 실행:

```sql
CREATE TABLE prediction_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    app_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    best_trigger TEXT NOT NULL,
    is_random BOOLEAN NOT NULL,
    trigger_scores JSONB,
    d3_purchase_prob FLOAT,
    d3_churn_prob FLOAT
);

-- 인덱스 (조회 성능)
CREATE INDEX idx_prediction_logs_app_id ON prediction_logs(app_id);
CREATE INDEX idx_prediction_logs_is_random ON prediction_logs(app_id, is_random);
CREATE INDEX idx_prediction_logs_timestamp ON prediction_logs(timestamp);
```

## 3. 환경변수 설정

Render 대시보드 → Environment → 아래 2개 추가:
- `SUPABASE_URL`: 프로젝트 Settings → API → Project URL
- `SUPABASE_KEY`: 프로젝트 Settings → API → anon/public key

## 4. 로컬 테스트

```bash
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="eyJxxx..."
uvicorn server.app:app --reload
```

## 5. 데이터 조회 (노트북에서)

```python
from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

# CATE 학습용: 랜덤 배정 유저만
data = client.table("prediction_logs").select("*").eq("app_id", "ablog").eq("is_random", True).execute()

# 전체 로그
data = client.table("prediction_logs").select("*").eq("app_id", "ablog").execute()
```
