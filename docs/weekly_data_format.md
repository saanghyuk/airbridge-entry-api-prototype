# 주간 학습 데이터 포맷

매주 노트북(`weekly_training.ipynb`)에서 사용할 CSV 파일 포맷입니다.

## 데이터 소스

```
Supabase (prediction_logs)     +     Snowflake (Airbridge DB)
  → trigger 배정 기록                  → UA features, In-app features, Outcomes
  → airbridge_uuid                    → airbridge_uuid
  → best_trigger, is_random           → modal_clicked, d3_purchase, d3_churn
          ↓                                     ↓
                    JOIN on airbridge_uuid
                            ↓
                    weekly_data.csv
```

## CSV 컬럼 (총 32개)

### 식별 (2개)
| 컬럼 | 타입 | 설명 | 소스 |
|------|------|------|------|
| `app_id` | string | 앱 식별자 | prediction_logs |
| `airbridge_uuid` | string | 유저 식별자 | prediction_logs + Snowflake |

### UA Features (15개) — Snowflake FMT 테이블에서 추출
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `trackinglink_count` | int | 트래킹 링크 터치 수 |
| `DA_count` | int | 디스플레이 광고 터치 수 |
| `SA_count` | int | 검색 광고 터치 수 |
| `unique_channel_count` | int | 채널 다양성 |
| `channel_entropy` | float | 채널 엔트로피 |
| `last_touch_is_da` | 0/1 | 마지막 터치가 DA인지 |
| `latency` | float | 첫 터치 → 설치 시간 (초) |
| `recency` | float | 마지막 터치 → 설치 시간 (초) |
| `recent_touch_pressure` | float | 최근 터치 밀도 |
| `touch_per_latency_hour` | float | 시간당 터치 빈도 |
| `last1h_touch_count` | int | 최근 1시간 터치 수 |
| `recent_24h_ratio` | float | 최근 24시간 터치 비율 |
| `click_ratio` | float | 클릭/노출 비율 |
| `impression_count` | int | 노출 수 |
| `is_single_touch_install` | 0/1 | 단일 터치 설치 여부 |

### In-app Features (10개) — Snowflake INTERNAL_MOBILE_EVENTS에서 추출 (첫 5분)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `product_viewed_count` | int | 상품 조회 수 |
| `user_signin` | 0/1 | 로그인 여부 |
| `product_addedtocart` | 0/1 | 장바구니 담기 |
| `deeplink_open` | 0/1 | 딥링크 유입 |
| `home_viewed` | 0/1 | 홈 화면 조회 |
| `addtowishlist` | 0/1 | 위시리스트 |
| `onboarding` | 0/1 | 온보딩 |
| `user_signup` | 0/1 | 회원가입 |
| `total_events` | int | 총 이벤트 수 |
| `n_event_types` | int | 이벤트 종류 수 |

### Trigger 배정 (2개) — Supabase prediction_logs에서
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `assigned_trigger` | string | 배정된 trigger (price_appeal/social_proof/scarcity/novelty) |
| `is_random` | 0/1 | 랜덤 배정 여부 (1이면 CATE 학습에 사용 가능) |

### Outcomes (3개) — Snowflake INTERNAL_MOBILE_EVENTS에서 추출
| 컬럼 | 타입 | 설명 | 수집 시점 |
|------|------|------|---------|
| `modal_clicked` | 0/1 | 모달 클릭 여부 (CATE primary outcome) | 즉시 |
| `d3_purchase` | 0/1 | 3일 내 구매 여부 | D3 후 |
| `d3_churn` | 0/1 | 3일 내 이탈 여부 | D3 후 |

## 데이터 수집 SQL 예시 (Snowflake)

### UA Features
```sql
-- Step 1-3: data_pipeline_guide.md 참조
-- FMT 테이블에서 journey JSON 추출 → Python에서 피처 엔지니어링
```

### In-app Features (첫 5분)
```sql
SELECT 
    DATA__DEVICE__AIRBRIDGEGENERATEDDEVICEUUID AS airbridge_uuid,
    DATA__EVENTDATA__GOAL__CATEGORY AS event_type,
    EVENT_TIMESTAMP
FROM AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS
WHERE DATA__APP__APPID = '{app_id}'
AND DATA__EVENTDATA__CATEGORY != '9161'  -- install 제외
AND TIMESTAMPDIFF(SECOND, install_timestamp, EVENT_TIMESTAMP) <= 300  -- 5분 이내
```

### Outcomes
```sql
-- 모달 클릭
SELECT 
    DATA__DEVICE__AIRBRIDGEGENERATEDDEVICEUUID AS airbridge_uuid,
    1 AS modal_clicked
FROM AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS
WHERE DATA__APP__APPID = '{app_id}'
AND DATA__EVENTDATA__GOAL__CATEGORY = 'entry_modal_clicked'

-- D3 구매
SELECT 
    DATA__DEVICE__AIRBRIDGEGENERATEDDEVICEUUID AS airbridge_uuid,
    1 AS d3_purchase
FROM AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS
WHERE DATA__APP__APPID = '{app_id}'
AND DATA__EVENTDATA__GOAL__CATEGORY IN ('purchase', 'order.completed')
AND TIMESTAMPDIFF(DAY, install_timestamp, EVENT_TIMESTAMP) <= 3
```

### Prediction Logs (Supabase)
```python
from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)
logs = client.table("prediction_logs") \
    .select("user_id, best_trigger, is_random, timestamp") \
    .eq("app_id", APP_ID) \
    .execute()

df_logs = pd.DataFrame(logs.data)
df_logs = df_logs.rename(columns={
    "user_id": "airbridge_uuid",
    "best_trigger": "assigned_trigger"
})
```

### 최종 JOIN
```python
# 1. Snowflake에서 features + outcomes 추출
df_features = pd.read_csv(f"data/{APP_ID}_features.csv")  # UA + In-app + outcomes

# 2. Supabase에서 trigger 배정 기록
df_logs = get_prediction_logs(APP_ID)

# 3. JOIN
df = df_features.merge(df_logs, on="airbridge_uuid", how="inner")

# 4. 저장
df.to_csv(f"data/weekly_data_{APP_ID}.csv", index=False)
```

## 주의사항

1. **is_random=1인 유저만 CATE 학습에 사용** — 80% 모델 추천 유저(is_random=0)는 D3 Purchase/Churn 학습에만 사용
2. **d3_purchase, d3_churn은 3일 후에 확정** — 최근 3일 이내 유저는 outcome이 아직 없음. 제외하거나 null 처리
3. **modal_clicked가 없는 유저** — API 호출은 됐지만 모달을 안 보여준 경우 (앱 크래시 등). 제외 처리
4. **airbridge_uuid 기준 중복 제거** — 같은 유저가 여러 번 API 호출될 수 있음. 첫 번째 기록만 사용
