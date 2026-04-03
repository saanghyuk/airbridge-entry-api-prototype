# 주간 학습 데이터 파이프라인

> **목적**: Airbridge Entry API 서비스의 주간 모델 재학습에 필요한 데이터를 Snowflake + Supabase에서 수집하는 전체 파이프라인
>
> **서비스가 사용하는 피처**: ~70개 (Device 7 + Install Time 6 + UA 47 + InApp 10)
> **Outcome**: 3개 (modal_clicked, d3_purchase, d3_churn)
> **Experiment**: 2개 (assigned_trigger, is_random) — Supabase에서 JOIN
>
> **검증 상태**: 모든 컬럼명, 이벤트명, JSON 키가 실제 Snowflake 샘플 데이터에서 검증됨
> (`query_and_sample/` 디렉토리의 CSV 파일 참조)
>
> 마지막 수정: 2026-04-02

---

## 1. 데이터 소스

### 1-1. Snowflake 테이블 (3개)

| # | 테이블 전체 이름 | 약칭 | 역할 | 컬럼 수 |
|---|-----------------|------|------|---------|
| 1 | `AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS` | MOBILE_EVENTS | 인앱 이벤트 로그 (install, open, purchase 등) | 265 |
| 2 | `AIRBRIDGE.PUBLIC.AIRBRIDGE_FMT_MOBILE_APP_EVENT_RESULTS_V20210802` | FMT_RESULTS | FMT attribution 결과 (UA 여정 JSON) | 16 |
| 3 | `AB180_X_FACEBOOK.PUBLIC.AIRBRIDGE_PLATFORM_MATCHED_TOUCHPOINTS_V20230410` | FB_TOUCHPOINTS | Facebook restricted 터치포인트 복원용 | 7 |

> **스키마 검증 완료**: 3개 테이블 모두 `SELECT * LIMIT 10`으로 샘플 확인.
> 샘플 데이터: `query_and_sample/AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS.csv` 등

#### MOBILE_EVENTS — 파이프라인에서 사용하는 컬럼 (검증됨)

| 용도 | 컬럼명 (정확히 이대로) |
|------|----------------------|
| 유저 ID | `DATA__DEVICE__AIRBRIDGEGENERATEDDEVICEUUID` |
| 앱 필터 | `DATA__APP__APPID` |
| 이벤트 코드 | `DATA__EVENTDATA__CATEGORY` — 9161=install, 9160=open, 9162=deeplink |
| 이벤트 이름 | `DATA__EVENTDATA__GOAL__CATEGORY` — `airbridge.ecommerce.product.viewed` 등 |
| 시간 | `EVENT_TIMESTAMP` |
| OS | `DATA__DEVICE__OSNAME` |
| OS 버전 | `DATA__DEVICE__OSVERSION` |
| 제조사 | `DATA__DEVICE__MANUFACTURER` |
| 언어 | `DATA__DEVICE__LANGUAGE` |
| 시간대 | `DATA__DEVICE__TIMEZONE` |
| 통신사 | `DATA__DEVICE__NETWORK__CARRIER` |
| 구매금액 | `DATA__EVENTDATA__GOAL__SEMANTICATTRIBUTES__TOTALVALUE` |
| 구매상품 | `DATA__EVENTDATA__GOAL__SEMANTICATTRIBUTES__PRODUCTS` |
| Custom Attrs | `DATA__EVENTDATA__GOAL__CUSTOMATTRIBUTES` — JSON string, `PARSE_JSON()` 사용 |

> **queryG2 검증**: commerce app(30778)의 purchase 이벤트에 `TOTALVALUE`가 없음 (모두 NULL). 금액 피처는 사용하지 않는다.

#### FMT_RESULTS — 파이프라인에서 사용하는 컬럼

| 용도 | 컬럼명 |
|------|--------|
| 여정 JSON | `DATA__ATTRIBUTIONRESULT` |
| 디바이스 JSON | `DATA__DEVICE` |
| 이벤트 코드 | `DATA__EVENTDATA__CATEGORY` |
| 시간 | `EVENT_TIMESTAMP` |
| 앱 필터 | `APP_ID` |

> **주의**: FMT 테이블의 `APP_ID`는 숫자, MOBILE_EVENTS의 `DATA__APP__APPID`도 숫자.

#### FB_TOUCHPOINTS — 파이프라인에서 사용하는 컬럼

| 용도 | 컬럼명 |
|------|--------|
| 터치포인트 JSON | `DATA` |
| 설치 시간 매칭 | `CONVERSION_EVENT_TIMESTAMP` |
| 터치포인트 시간 | `TOUCHPOINT_EVENT_TIMESTAMP` |
| 앱 필터 | `APP_ID` |

> **queryI 검증**: 267,849개의 restricted 터치포인트가 존재. FB 테이블로 복원 필수.
>
> **FB JSON 키** (검증됨): `touchpoint__channel`, `touchpoint__interactionType`, `touchpoint__campaign`, `touchpoint__adCreative`, `conversion__deviceUUID`

### 1-2. Supabase

| 테이블 | 용도 | 주요 컬럼 |
|--------|------|-----------|
| `prediction_logs` | API 호출 시 서버가 기록한 trigger 배정 결과 | `airbridge_uuid`, `best_trigger` (-> assigned_trigger), `is_random`, `timestamp` |

---

## 2. 앱별 이벤트 매핑 시스템

### 2-1. Config 파일 구조

이벤트 매핑은 `configs/{app_id}.json`에 저장. 기본값은 `configs/default_commerce.json`.

```
configs/
  ├── default_commerce.json   — 커머스 앱 기본 템플릿 (app_id: null)
  └── ablog.json              — app_id: 30778 (Ablog/Athler)
```

새 앱을 추가할 때: `default_commerce.json`을 복사 -> `app_id`와 `app_name` 수정 -> 앱 고유 이벤트가 있으면 `event_mapping` 수정.

### 2-2. Config 주요 필드

```json
{
  "app_id": "30778",
  "app_name": "ablog",
  "event_mapping": {
    "product_viewed": "airbridge.ecommerce.product.viewed",
    "home_viewed": "airbridge.ecommerce.home.viewed",
    "addedtocart": "airbridge.ecommerce.product.addedToCart",
    "addtowishlist": "airbridge.addToWishlist",
    "signin": "airbridge.user.signin",
    "signup": "airbridge.user.signup",
    "onboarding": "airbridge.onboarding",
    "purchase": "airbridge.ecommerce.order.completed",
    "modal_clicked": "entry_modal_clicked",
    "deeplink_open_category": "9162"
  },
  "event_category_codes": {
    "install": "9161",
    "open": "9160",
    "deeplink_open": "9162",
    "custom_event": "9360"
  },
  "leakage_events": [
    "airbridge.ecommerce.order.completed",
    "airbridge.ecommerce.order.canceled",
    "airbridge.initiateCheckout"
  ]
}
```

### 2-3. Commerce App (30778) 이벤트 분포 (queryC2 검증)

| 이벤트 | `DATA__EVENTDATA__GOAL__CATEGORY` 값 (정확히) | 건수 |
|--------|----------------------------------------------|------|
| product_viewed | `airbridge.ecommerce.product.viewed` | 34,652,715 |
| home_viewed | `airbridge.ecommerce.home.viewed` | 11,604,728 |
| addedtocart | `airbridge.ecommerce.product.addedToCart` | 1,403,874 |
| addtowishlist | `airbridge.addToWishlist` | 748,884 |
| purchase | `airbridge.ecommerce.order.completed` | 424,265 |
| signin | `airbridge.user.signin` | 263,730 |
| onboarding | `airbridge.onboarding` | 73,801 |
| signup | `airbridge.user.signup` | 38,737 |

> **주의**: `purchase`가 아니라 `airbridge.ecommerce.order.completed`이다. prefix 포함.

### 2-4. 이벤트 카테고리 코드 (queryD2, queryF 검증)

| 코드 | 의미 | `DATA__EVENTDATA__CATEGORY` | `DATA__EVENTDATA__GOAL__CATEGORY` |
|------|------|---------------------------|-----------------------------------|
| 9161 | install | `9161` | -- |
| 9160 | open | `9160` | -- |
| 9162 | deeplink_open | `9162` | -- |
| 9360 | custom event | `9360$$<event_name>` | `<event_name>` |

> **queryF 검증**: install=12,913,682건, open=1,805,084,652건

### 2-5. 터치포인트 JSON 구조 (query2 검증)

#### Journey JSON (`DATA__ATTRIBUTIONRESULT`)

```json
{
  "attributedChannel": "facebook",
  "attributedAdCreative": "120229198116110476",
  "assistedTouchpoints": [
    {
      "channel": "apple.searchads",
      "interaction_type": "click",
      "term": "골프웨어",
      "timestamp": 1767231101027,
      "ad_creative": "...",
      "campaign": "...",
      "ad_group": "...",
      "content": "...",
      "medium": "...",
      "matching_type": "...",
      "device": "...",
      "future_time_fraud_type": 0,
      "fraud_tag_list": []
    }
  ]
}
```

#### 터치포인트 JSON 키 전체 목록 (query2에서 검증)

```
ad_creative, ad_group, attr_score, campaign, channel, client_id, content,
device, event_category, event_category_type, event_uuid, fraud_tag_list,
future_time_fraud_type, interaction_type, is_estimated_timestamp,
is_reengagement, matching_type, medium, not_attributed_reason,
original_timestamp, short_id, sl_gen_type, sl_type, source_table,
sub_id_1, sub_id_2, term, term_id, timestamp
```

> **중요**: `ad_creative`이다. `adcreative`가 아님. query2에서 직접 확인됨.

#### Fraud Type 분포 (queryB 검증)

| future_time_fraud_type | 건수 | 설명 |
|------------------------|------|------|
| NULL | 8,977,131 | 미확인 |
| 0 | 5,307,496 | 정상 |
| 1 | 3,660 | fraud |
| 2 | 3,086 | fraud |
| 3 | 18,274 | fraud |
| 4 | 2,830 | fraud |

> fraud 터치포인트: `future_time_fraud_type != 0 AND future_time_fraud_type IS NOT NULL`인 경우.

---

## 3. Feature 목록 (~70개)

### Group A: Device 피처 (7개)

설치 시점의 디바이스 정보. install 이벤트(`DATA__EVENTDATA__CATEGORY = '9161'`) 행에서 추출.

| # | 피처명 | 소스 컬럼 (MOBILE_EVENTS) | 타입 |
|---|--------|--------------------------|------|
| 1 | `OS_NAME` | `DATA__DEVICE__OSNAME` | categorical |
| 2 | `DEVICE_MANUFACTURER` | `DATA__DEVICE__MANUFACTURER` | categorical |
| 3 | `DEVICE_LANGUAGE` | `DATA__DEVICE__LANGUAGE` | categorical |
| 4 | `DEVICE_TIMEZONE` | `DATA__DEVICE__TIMEZONE` | categorical |
| 5 | `DEVICE_OSVERSION` | `DATA__DEVICE__OSVERSION` | categorical |
| 6 | `DEVICE_CARRIER` | `DATA__DEVICE__NETWORK__CARRIER` | categorical |
| 7 | `IS_HAS_FRAUD` | Step 14에서 계산 | 0/1 |

### Group B: Install Time 피처 (6개)

`EVENT_TIMESTAMP`의 hour를 추출 -> 6개 시간대 bin.

| # | 피처명 | 시간대 | 타입 |
|---|--------|--------|------|
| 1 | `is_installed_02_06` | 02:00~05:59 | 0/1 |
| 2 | `is_installed_06_10` | 06:00~09:59 | 0/1 |
| 3 | `is_installed_10_14` | 10:00~13:59 | 0/1 |
| 4 | `is_installed_14_18` | 14:00~17:59 | 0/1 |
| 5 | `is_installed_18_22` | 18:00~21:59 | 0/1 |
| 6 | `is_installed_22_02` | 22:00~01:59 | 0/1 |

### Group C: UA 피처 (47개)

`DATA__ATTRIBUTIONRESULT` (journey JSON)에서 Python으로 계산. Facebook 터치포인트 복원 (Step 12-13) 후 계산.

#### C-1. 바이너리 (13개)

| # | 피처명 | 설명 |
|---|--------|------|
| 1 | `has_touchpoint` | assistedTouchpoints 존재 여부 |
| 2 | `has_last_touch` | 라스트 터치 존재 여부 |
| 3 | `last_touch_is_trackinglink` | 라스트 터치 채널 타입 = trackinglink |
| 4 | `last_touch_is_da` | 라스트 터치 채널 타입 = DA |
| 5 | `last_touch_is_sa` | 라스트 터치 채널 타입 = SA |
| 6 | `has_term` | 검색 키워드(`term`) 존재 여부 |
| 7 | `is_single_touch_install` | 터치포인트 1개만 (len == 1) |
| 8 | `first_is_click` | 첫 터치 `interaction_type` == click |
| 9 | `first_is_impression` | 첫 터치 `interaction_type` == impression |
| 10 | `last_is_click` | 마지막 터치 `interaction_type` == click |
| 11 | `last_is_impression` | 마지막 터치 `interaction_type` == impression |
| 12 | `has_gm_touchpoint` | Google/Meta 터치포인트 존재 (channel에 google/meta/facebook 포함) |
| 13 | `media_type` | 라스트 터치 채널 -> SA/DA/Trackinglink/Organic (categorical) |

#### C-2. 시간 (9개)

| # | 피처명 | 설명 | 계산 |
|---|--------|------|------|
| 1 | `latency` | 첫 터치 -> 설치 시간 (초) | `(install_ts - first_tp_ts) / 1000` |
| 2 | `recency` | 마지막 터치 -> 설치 시간 (초) | `(install_ts - last_tp_ts) / 1000` |
| 3 | `touch_window` | 첫 터치 -> 마지막 터치 시간 (초) | `(last_tp_ts - first_tp_ts) / 1000` |
| 4 | `recent_touch_pressure` | 최근 터치 밀도 | `(last1h / max(total, 1)) * (total / max(latency_hours, 1))` |
| 5 | `recent_24h_ratio` | 최근 24시간 터치 비율 | `last24h / max(total, 1)` |
| 6 | `recent_24h_multiple` | 최근 24시간 터치 배수 | `last24h / max(before24h, 1)` |
| 7 | `touch_per_window_hour` | 윈도우 시간당 터치 수 | `total / max(window_hours, 1)` |
| 8 | `touch_per_latency_day` | latency 일 대비 터치 밀도 | `total / max(latency_days, 1)` |
| 9 | `touch_per_latency_hour` | latency 시간 대비 터치 밀도 | `total / max(latency_hours, 1)` |

#### C-3. 카운트 (13개)

| # | 피처명 | 설명 |
|---|--------|------|
| 1 | `DA_count` | DA 채널 터치포인트 수 |
| 2 | `SA_count` | SA 채널 터치포인트 수 |
| 3 | `trackinglink_count` | Trackinglink 채널 터치포인트 수 |
| 4 | `total_touch_count` | 전체 터치포인트 수 |
| 5 | `unique_channel_count` | 고유 채널 수 |
| 6 | `click_count` | click 인터랙션 수 |
| 7 | `impression_count` | impression 인터랙션 수 |
| 8 | `click_ratio` | click / max(click + impression, 1) |
| 9 | `term_total_count` | 검색 키워드(`term`) 총 수 |
| 10 | `term_unique_count` | 고유 검색 키워드 수 |
| 11 | `last30min_touch_count` | 설치 전 30분 이내 터치 수 |
| 12 | `last1h_touch_count` | 설치 전 1시간 이내 터치 수 |
| 13 | `last3h_touch_count` | 설치 전 3시간 이내 터치 수 |

#### C-4. 비율 (4개)

| # | 피처명 | 설명 |
|---|--------|------|
| 1 | `touch_count_ratio_0_30m` | 0~30분 터치 비율 |
| 2 | `touch_count_ratio_30m_1h` | 30분~1시간 터치 비율 |
| 3 | `touch_count_ratio_0_1h` | 0~1시간 터치 비율 |
| 4 | `touch_count_ratio_1h_3h` | 1~3시간 터치 비율 |

#### C-5. 기타 (2개)

| # | 피처명 | 설명 |
|---|--------|------|
| 1 | `channel_entropy` | 채널 다양성 (Shannon entropy): `-sum(p * log(p))` |
| 2 | `touchpoint_sequence` | 터치포인트 시퀀스 JSON (향후 시퀀스 모델용, 모델 input에는 미포함) |

#### C-6. 키워드 (4개)

`sa_term_list`에서 추출. 앱별로 `keyword_classification` 커스터마이즈 필요.

| # | 피처명 | 설명 |
|---|--------|------|
| 1 | `kw_brand_search` | 브랜드 키워드 포함 여부 |
| 2 | `kw_product_search` | 상품 키워드 포함 여부 |
| 3 | `kw_promo_season_search` | 프로모션/시즌 키워드 포함 여부 |
| 4 | `keyword_list` | 전체 키워드 리스트 (모델 input에는 미포함) |

### Group D: InApp 5분 피처 (10개)

설치 후 5분(300초) 이내 이벤트를 집계. 이벤트명은 `configs/{app_id}.json`의 `inapp_feature_mapping`에서 로드.

| # | 피처명 | config key | Snowflake 이벤트 조건 | 타입 |
|---|--------|-----------|----------------------|------|
| 1 | `product_viewed_count` | `product_viewed` | `GOAL_CATEGORY = 'airbridge.ecommerce.product.viewed'` | COUNT |
| 2 | `user_signin` | `signin` | `GOAL_CATEGORY = 'airbridge.user.signin'` | 0/1 |
| 3 | `product_addedtocart` | `addedtocart` | `GOAL_CATEGORY = 'airbridge.ecommerce.product.addedToCart'` | 0/1 |
| 4 | `deeplink_open` | `deeplink_open_category` | `DATA__EVENTDATA__CATEGORY = '9162'` | 0/1 |
| 5 | `home_viewed` | `home_viewed` | `GOAL_CATEGORY = 'airbridge.ecommerce.home.viewed'` | 0/1 |
| 6 | `addtowishlist` | `addtowishlist` | `GOAL_CATEGORY = 'airbridge.addToWishlist'` | 0/1 |
| 7 | `onboarding` | `onboarding` | `GOAL_CATEGORY = 'airbridge.onboarding'` | 0/1 |
| 8 | `user_signup` | `signup` | `GOAL_CATEGORY = 'airbridge.user.signup'` | 0/1 |
| 9 | `total_events` | -- | install/leakage 제외 전체 이벤트 수 | COUNT |
| 10 | `n_event_types` | -- | 고유 이벤트 타입 수 (leakage 제외) | COUNT |

> **Leakage 이벤트** (제외): config의 `leakage_events` 참조. 기본값: `airbridge.ecommerce.order.completed`, `airbridge.initiateCheckout` -- 구매 자체가 outcome이므로 input에서 제거.

### Group E: Experiment 피처 (2개)

Supabase `prediction_logs`에서 JOIN.

| # | 피처명 | Supabase 컬럼 | 설명 |
|---|--------|---------------|------|
| 1 | `assigned_trigger` | `prediction_logs.best_trigger` | 배정된 trigger |
| 2 | `is_random` | `prediction_logs.is_random` | 랜덤 배정 여부 (true -> CATE 학습 가능) |

### Group F: Outcome (3개)

| # | 피처명 | 조건 | 수집 시점 |
|---|--------|------|-----------|
| 1 | `modal_clicked` | `GOAL_CATEGORY = 'entry_modal_clicked'` (커스텀 SDK 이벤트) | 즉시 |
| 2 | `d3_purchase` | `GOAL_CATEGORY = 'airbridge.ecommerce.order.completed'` AND 설치 후 3일 이내 | D3 후 |
| 3 | `d3_churn` | 마지막 활동 시점이 설치 후 3일 이내 (= 3일 넘게 비활동) | D3 후 |

> **중요**: purchase 이벤트는 `'airbridge.ecommerce.order.completed'`이다. `'purchase'`가 아님.

### 피처 요약

| 그룹 | 피처 수 | 소스 |
|------|---------|------|
| A: Device | 7 | MOBILE_EVENTS (install 행) |
| B: Install Time | 6 | install `EVENT_TIMESTAMP` -> Python |
| C: UA | 47 | FMT_RESULTS journey JSON + FB_TOUCHPOINTS 복원 -> Python |
| D: InApp 5min | 10 | MOBILE_EVENTS (5분 윈도우) -> SQL + Python |
| E: Experiment | 2 | Supabase prediction_logs |
| F: Outcome | 3 | MOBILE_EVENTS (D3 window) |
| **합계** | **~75** | |

---

## 4. SQL 쿼리 (검증된 컬럼명)

원본 15 step 중 필요한 것만 추출. 모든 컬럼명이 실제 샘플 데이터와 검증됨.

> **새 앱 적용 시 변경점**: `app_id` 필터값, 이벤트 매핑 (config에서 로드), 채널 분류 CASE WHEN.

### Step 1: install_users -- 설치 유저 추출

```sql
CREATE TEMPORARY TABLE install_users AS
SELECT
    DATA__DEVICE__AIRBRIDGEGENERATEDDEVICEUUID AS user_id,
    MIN(EVENT_TIMESTAMP) AS install_ts,
    -- Device 피처 (install 이벤트 행에서 추출)
    MAX(DATA__DEVICE__OSNAME) AS OS_NAME,
    MAX(DATA__DEVICE__MANUFACTURER) AS DEVICE_MANUFACTURER,
    MAX(DATA__DEVICE__LANGUAGE) AS DEVICE_LANGUAGE,
    MAX(DATA__DEVICE__TIMEZONE) AS DEVICE_TIMEZONE,
    MAX(DATA__DEVICE__OSVERSION) AS DEVICE_OSVERSION,
    MAX(DATA__DEVICE__NETWORK__CARRIER) AS DEVICE_CARRIER
FROM AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS
WHERE DATA__APP__APPID = :app_id
  AND DATA__EVENTDATA__CATEGORY = '9161'  -- install (queryF 검증)
  AND EVENT_TIMESTAMP >= :start_date
  AND EVENT_TIMESTAMP < :end_date
GROUP BY 1;
```

### Step 2: fmt_flat -- UA attribution 결과 추출

```sql
CREATE TEMPORARY TABLE fmt_flat AS
SELECT
    DATA__DEVICE:airbridgeGeneratedDeviceUUID::STRING AS user_id,
    DATA__ATTRIBUTIONRESULT AS journey_json,
    EVENT_TIMESTAMP AS fmt_ts
FROM AIRBRIDGE.PUBLIC.AIRBRIDGE_FMT_MOBILE_APP_EVENT_RESULTS_V20210802
WHERE APP_ID = :app_id
  AND DATA__EVENTDATA__CATEGORY = '9161'
QUALIFY ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY fmt_ts DESC) = 1;
```

### Step 3: ua_table -- 유저 기본 테이블

```sql
CREATE TEMPORARY TABLE ua_table AS
SELECT
    iu.user_id,
    iu.install_ts,
    iu.OS_NAME,
    iu.DEVICE_MANUFACTURER,
    iu.DEVICE_LANGUAGE,
    iu.DEVICE_TIMEZONE,
    iu.DEVICE_OSVERSION,
    iu.DEVICE_CARRIER,
    ff.journey_json
FROM install_users iu
LEFT JOIN fmt_flat ff ON iu.user_id = ff.user_id;
```

### Step 4: inapp_base -- 인앱 이벤트 추출

```sql
CREATE TEMPORARY TABLE inapp_base AS
SELECT
    ev.DATA__DEVICE__AIRBRIDGEGENERATEDDEVICEUUID AS user_id,
    ev.DATA__EVENTDATA__CATEGORY AS evt_cat,
    ev.DATA__EVENTDATA__GOAL__CATEGORY AS goal_cat,
    ev.EVENT_TIMESTAMP,
    TIMESTAMPDIFF(SECOND, iu.install_ts, ev.EVENT_TIMESTAMP) AS sec_after
FROM AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS ev
INNER JOIN install_users iu
    ON ev.DATA__DEVICE__AIRBRIDGEGENERATEDDEVICEUUID = iu.user_id
WHERE ev.DATA__APP__APPID = :app_id
  AND ev.EVENT_TIMESTAMP >= iu.install_ts
  AND ev.EVENT_TIMESTAMP <= DATEADD(DAY, 30, iu.install_ts);
```

### Step 5: user_churn_base -- 이탈 기준

```sql
CREATE TEMPORARY TABLE user_churn_base AS
SELECT
    user_id,
    MAX(sec_after) AS seconds_active_after_install
FROM inapp_base
GROUP BY 1;
```

### Step 6: inapp_agg_5min -- 인앱 이벤트 5분 윈도우 집계

이벤트 이름은 앱별 config의 `event_mapping`에서 로드. 아래는 commerce app 기본값.

```sql
CREATE TEMPORARY TABLE inapp_agg_5min AS
SELECT
    user_id,

    -- InApp 5분 피처 (이벤트명은 queryC2에서 검증됨)
    COUNT(CASE WHEN goal_cat = 'airbridge.ecommerce.product.viewed'
               AND sec_after <= 300 THEN 1 END) AS product_viewed_count,
    MAX(CASE WHEN goal_cat = 'airbridge.user.signin'
             AND sec_after <= 300 THEN 1 ELSE 0 END) AS user_signin,
    MAX(CASE WHEN goal_cat = 'airbridge.ecommerce.product.addedToCart'
             AND sec_after <= 300 THEN 1 ELSE 0 END) AS product_addedtocart,
    MAX(CASE WHEN evt_cat = '9162'
             AND sec_after <= 300 THEN 1 ELSE 0 END) AS deeplink_open,
    MAX(CASE WHEN goal_cat = 'airbridge.ecommerce.home.viewed'
             AND sec_after <= 300 THEN 1 ELSE 0 END) AS home_viewed,
    MAX(CASE WHEN goal_cat = 'airbridge.addToWishlist'
             AND sec_after <= 300 THEN 1 ELSE 0 END) AS addtowishlist,
    MAX(CASE WHEN goal_cat = 'airbridge.onboarding'
             AND sec_after <= 300 THEN 1 ELSE 0 END) AS onboarding,
    MAX(CASE WHEN goal_cat = 'airbridge.user.signup'
             AND sec_after <= 300 THEN 1 ELSE 0 END) AS user_signup,

    -- total_events: install/leakage 제외, 5분 이내
    COUNT(CASE WHEN sec_after <= 300
               AND evt_cat != '9161'
               AND COALESCE(goal_cat, '') != 'airbridge.ecommerce.order.completed'
               AND COALESCE(goal_cat, '') != 'airbridge.initiateCheckout'
               THEN 1 END) AS total_events,

    -- n_event_types: 고유 이벤트 타입 수 (5분 이내, leakage 제외)
    COUNT(DISTINCT CASE WHEN sec_after <= 300
                        AND evt_cat != '9161'
                        AND COALESCE(goal_cat, '') != 'airbridge.ecommerce.order.completed'
                        AND COALESCE(goal_cat, '') != 'airbridge.initiateCheckout'
                        THEN COALESCE(goal_cat, evt_cat) END) AS n_event_types,

    -- === Outcomes ===
    MAX(CASE WHEN goal_cat = 'entry_modal_clicked' THEN 1 ELSE 0 END) AS modal_clicked,
    MAX(CASE WHEN goal_cat = 'airbridge.ecommerce.order.completed'
             AND sec_after <= 259200  -- 3일 = 259,200초
             THEN 1 ELSE 0 END) AS d3_purchase

FROM inapp_base
GROUP BY 1;
```

### Step 12-13: Facebook 터치포인트 복원

```sql
-- Step 12a: journey에서 channel='restricted'인 유저 추출
CREATE TEMPORARY TABLE restricted_users AS
SELECT
    ut.user_id,
    ut.install_ts,
    ut.journey_json
FROM ua_table ut
WHERE ut.journey_json LIKE '%"restricted"%';

-- Step 12b: Facebook 터치포인트 매칭
CREATE TEMPORARY TABLE restricted_fixed AS
SELECT
    ru.user_id,
    fb.DATA AS meta_touchpoint
FROM restricted_users ru
INNER JOIN AB180_X_FACEBOOK.PUBLIC.AIRBRIDGE_PLATFORM_MATCHED_TOUCHPOINTS_V20230410 fb
    ON fb.APP_ID = :app_id
    AND fb.CONVERSION_EVENT_TIMESTAMP = ru.install_ts;

-- Step 13: ua_table에 Facebook 터치포인트 합치기
CREATE TEMPORARY TABLE ua_table_enriched AS
SELECT
    ut.*,
    rf.meta_touchpoint
FROM ua_table ut
LEFT JOIN restricted_fixed rf ON ut.user_id = rf.user_id;
```

### Step 14: 채널 분류 + Fraud 제거

```sql
CREATE TEMPORARY TABLE touchpoint_analysis AS
SELECT
    ue.user_id,

    -- 채널 분류 (터치포인트 JSON key = query2에서 검증)
    COUNT(CASE WHEN tp.value:channel::STRING IN ('apple.searchads', 'google.searchads', 'naver_sa', 'kakao_sa')
               OR tp.value:channel::STRING LIKE '%searchads%'
               THEN 1 END) AS sa_tp_count,
    COUNT(CASE WHEN tp.value:channel::STRING IN ('facebook', 'meta', 'google', 'naver_gfa', 'kakao_moment',
                                                   'kakao_bizboard', 'tiktok', 'criteo', 'rtbhouse',
                                                   'moloco', 'applovin', 'remerge', 'adn')
               OR tp.value:channel::STRING LIKE '%facebook%'
               OR tp.value:channel::STRING LIKE '%meta%'
               OR tp.value:channel::STRING LIKE '%google%'
               THEN 1 END) AS da_tp_count,

    -- Fraud 판별 (future_time_fraud_type -- query2에서 키 존재 확인, queryB에서 분포 확인)
    MAX(CASE WHEN tp.value:future_time_fraud_type::INT != 0
             AND tp.value:future_time_fraud_type IS NOT NULL
             THEN 1 ELSE 0 END) AS IS_HAS_FRAUD,
    SUM(CASE WHEN tp.value:future_time_fraud_type::INT != 0
             AND tp.value:future_time_fraud_type IS NOT NULL
             THEN 1 ELSE 0 END) AS fraud_count,

    -- SA 키워드 수집 (term -- query1, query2에서 검증)
    ARRAY_AGG(DISTINCT tp.value:term::STRING) FILTER (
        WHERE tp.value:term::STRING IS NOT NULL
        AND tp.value:term::STRING != ''
    ) AS sa_term_list

FROM ua_table_enriched ue,
     LATERAL FLATTEN(input => PARSE_JSON(ue.journey_json):assistedTouchpoints, outer => true) tp
GROUP BY ue.user_id;
```

> **채널 분류 주의**: 앱마다 DA/SA 채널 매핑이 다를 수 있다. `configs/{app_id}.json`의 `channel_classification` 참조.

### 최종 결합 쿼리

```sql
SELECT
    :app_id AS app_id,
    ue.user_id AS airbridge_uuid,
    ue.install_ts,

    -- Group A: Device (7)
    ue.OS_NAME,
    ue.DEVICE_MANUFACTURER,
    ue.DEVICE_LANGUAGE,
    ue.DEVICE_TIMEZONE,
    ue.DEVICE_OSVERSION,
    ue.DEVICE_CARRIER,

    -- Journey JSON (Python에서 Group B + C 피처로 변환)
    ue.journey_json,
    ue.meta_touchpoint,

    -- Group D: InApp 5min (10)
    COALESCE(ia.product_viewed_count, 0) AS product_viewed_count,
    COALESCE(ia.user_signin, 0) AS user_signin,
    COALESCE(ia.product_addedtocart, 0) AS product_addedtocart,
    COALESCE(ia.deeplink_open, 0) AS deeplink_open,
    COALESCE(ia.home_viewed, 0) AS home_viewed,
    COALESCE(ia.addtowishlist, 0) AS addtowishlist,
    COALESCE(ia.onboarding, 0) AS onboarding,
    COALESCE(ia.user_signup, 0) AS user_signup,
    COALESCE(ia.total_events, 0) AS total_events,
    COALESCE(ia.n_event_types, 0) AS n_event_types,

    -- Outcomes (3)
    COALESCE(ia.modal_clicked, 0) AS modal_clicked,
    COALESCE(ia.d3_purchase, 0) AS d3_purchase,
    CASE WHEN COALESCE(uc.seconds_active_after_install, 0) <= 259200
         THEN 1 ELSE 0 END AS d3_churn,

    -- Fraud 정보
    COALESCE(ta.IS_HAS_FRAUD, 0) AS IS_HAS_FRAUD,
    ta.sa_term_list

FROM ua_table_enriched ue
LEFT JOIN inapp_agg_5min ia ON ue.user_id = ia.user_id
LEFT JOIN user_churn_base uc ON ue.user_id = uc.user_id
LEFT JOIN touchpoint_analysis ta ON ue.user_id = ta.user_id;
```

---

## 5. Python 피처 엔지니어링

`run_analysis.py`의 로직을 서비스용으로 정리. SQL 결과의 JSON 컬럼들을 flat 피처로 변환.

### 5-1. 채널 분류

```python
import json

def load_channel_config(config_path: str) -> tuple[list, list]:
    """앱별 config에서 채널 분류 키워드 로드."""
    with open(config_path) as f:
        config = json.load(f)
    cc = config.get('channel_classification', {})
    return cc.get('sa_keywords', []), cc.get('da_keywords', [])

# Default keywords
DA_KEYWORDS = [
    'facebook', 'meta', 'google', 'naver_gfa', 'kakao_moment',
    'kakao_bizboard', 'tiktok', 'criteo', 'rtbhouse', 'moloco',
    'applovin', 'remerge', 'adn',
]
SA_KEYWORDS = [
    'apple.searchads', 'searchads', 'google.searchads',
    'naver_sa', 'kakao_sa',
]

def classify_channel(channel: str) -> str:
    """Classify a touchpoint channel as SA / DA / trackinglink."""
    if not channel:
        return 'trackinglink'
    ch = channel.lower()
    for kw in SA_KEYWORDS:
        if kw in ch:
            return 'SA'
    for kw in DA_KEYWORDS:
        if kw in ch:
            return 'DA'
    return 'trackinglink'
```

### 5-2. Facebook 터치포인트 복원

```python
def restore_facebook_touchpoints(journey_json: str, meta_touchpoint: str) -> dict:
    """
    Journey JSON의 'restricted' 터치포인트를 Facebook 실제 터치포인트로 교체.

    FB JSON 키 (검증됨):
      touchpoint__channel, touchpoint__interactionType,
      touchpoint__campaign, touchpoint__adCreative,
      conversion__deviceUUID
    """
    if not journey_json or journey_json == 'null':
        return {}

    try:
        journey = json.loads(journey_json) if isinstance(journey_json, str) else journey_json
    except (json.JSONDecodeError, TypeError):
        return {}

    if not meta_touchpoint or meta_touchpoint == 'null':
        return journey

    try:
        fb_data = json.loads(meta_touchpoint) if isinstance(meta_touchpoint, str) else meta_touchpoint
    except (json.JSONDecodeError, TypeError):
        return journey

    touchpoints = journey.get('assistedTouchpoints', [])
    restored = []
    for tp in touchpoints:
        if tp.get('channel', '') == 'restricted':
            fb_tp = dict(tp)
            if isinstance(fb_data, dict):
                # FB JSON 키 매핑 (검증됨)
                fb_tp['channel'] = fb_data.get('touchpoint__channel', 'facebook')
                fb_tp['interaction_type'] = fb_data.get('touchpoint__interactionType',
                                                         tp.get('interaction_type', ''))
                fb_tp['campaign'] = fb_data.get('touchpoint__campaign', '')
                fb_tp['ad_creative'] = fb_data.get('touchpoint__adCreative', '')
            restored.append(fb_tp)
        else:
            restored.append(tp)

    journey['assistedTouchpoints'] = restored
    return journey
```

### 5-3. UA 47개 피처 계산

```python
import math
from collections import Counter

def parse_journey(journey: dict, install_ts_ms: int) -> dict:
    """
    Journey dict에서 47개 UA 피처를 계산.
    터치포인트 JSON 키: channel, interaction_type, term, timestamp,
    ad_creative, campaign, future_time_fraud_type 등 (query2 검증).
    """
    result = {
        # Binary (13)
        'has_touchpoint': 0, 'has_last_touch': 0,
        'last_touch_is_trackinglink': 0, 'last_touch_is_da': 0, 'last_touch_is_sa': 0,
        'has_term': 0, 'is_single_touch_install': 0,
        'first_is_click': 0, 'first_is_impression': 0,
        'last_is_click': 0, 'last_is_impression': 0,
        'has_gm_touchpoint': 0, 'media_type': 'Organic',
        # Temporal (9)
        'latency': 0.0, 'recency': 0.0, 'touch_window': 0.0,
        'recent_touch_pressure': 0.0, 'recent_24h_ratio': 0.0,
        'recent_24h_multiple': 0.0, 'touch_per_window_hour': 0.0,
        'touch_per_latency_day': 0.0, 'touch_per_latency_hour': 0.0,
        # Count (13)
        'DA_count': 0, 'SA_count': 0, 'trackinglink_count': 0,
        'total_touch_count': 0, 'unique_channel_count': 0,
        'click_count': 0, 'impression_count': 0, 'click_ratio': 0.0,
        'term_total_count': 0, 'term_unique_count': 0,
        'last30min_touch_count': 0, 'last1h_touch_count': 0, 'last3h_touch_count': 0,
        # Ratio (4)
        'touch_count_ratio_0_30m': 0.0, 'touch_count_ratio_30m_1h': 0.0,
        'touch_count_ratio_0_1h': 0.0, 'touch_count_ratio_1h_3h': 0.0,
        # Other (2)
        'channel_entropy': 0.0, 'touchpoint_sequence': '[]',
    }

    if not journey:
        return result

    touchpoints = journey.get('assistedTouchpoints', [])
    if not touchpoints:
        return result

    n = len(touchpoints)
    result['has_touchpoint'] = 1
    result['total_touch_count'] = n
    result['is_single_touch_install'] = 1 if n == 1 else 0

    channels, channel_types = [], []
    click_count, imp_count = 0, 0
    timestamps, terms, sequence = [], [], []
    last30min_count = last1h_count = last3h_count = last24h_count = 0

    for tp in touchpoints:
        ch = tp.get('channel', '')
        channels.append(ch)
        ch_type = classify_channel(ch)
        channel_types.append(ch_type)

        ch_lower = ch.lower()
        if any(kw in ch_lower for kw in ['google', 'meta', 'facebook']):
            result['has_gm_touchpoint'] = 1

        itype = (tp.get('interaction_type', '') or '').lower()
        if itype == 'click':
            click_count += 1
        elif itype == 'impression':
            imp_count += 1

        # term (query1, query2 검증: 'term' key exists in touchpoints)
        term = tp.get('term', '')
        if term:
            terms.append(term)

        ts = tp.get('timestamp', 0)
        if ts:
            timestamps.append(ts)
            sec_before = (install_ts_ms - ts) / 1000.0
            if sec_before <= 1800: last30min_count += 1
            if sec_before <= 3600: last1h_count += 1
            if sec_before <= 10800: last3h_count += 1
            if sec_before <= 86400: last24h_count += 1

        sequence.append({'channel': ch, 'type': ch_type, 'interaction': itype})

    type_counts = Counter(channel_types)
    result['DA_count'] = type_counts.get('DA', 0)
    result['SA_count'] = type_counts.get('SA', 0)
    result['trackinglink_count'] = type_counts.get('trackinglink', 0)
    result['unique_channel_count'] = len(set(channels))

    if n > 0:
        ch_counts = Counter(channels)
        probs = [c / n for c in ch_counts.values()]
        result['channel_entropy'] = -sum(p * math.log(p) for p in probs if p > 0)

    result['click_count'] = click_count
    result['impression_count'] = imp_count
    result['click_ratio'] = click_count / max(click_count + imp_count, 1)

    if channel_types:
        last_type = channel_types[-1]
        result['has_last_touch'] = 1
        result['last_touch_is_da'] = 1 if last_type == 'DA' else 0
        result['last_touch_is_sa'] = 1 if last_type == 'SA' else 0
        result['last_touch_is_trackinglink'] = 1 if last_type == 'trackinglink' else 0
        result['media_type'] = last_type

    first_itype = (touchpoints[0].get('interaction_type', '') or '').lower()
    last_itype = (touchpoints[-1].get('interaction_type', '') or '').lower()
    result['first_is_click'] = 1 if first_itype == 'click' else 0
    result['first_is_impression'] = 1 if first_itype == 'impression' else 0
    result['last_is_click'] = 1 if last_itype == 'click' else 0
    result['last_is_impression'] = 1 if last_itype == 'impression' else 0

    result['has_term'] = 1 if terms else 0
    result['term_total_count'] = len(terms)
    result['term_unique_count'] = len(set(terms))

    result['last30min_touch_count'] = last30min_count
    result['last1h_touch_count'] = last1h_count
    result['last3h_touch_count'] = last3h_count

    if timestamps:
        first_ts, last_ts = min(timestamps), max(timestamps)
        latency = max((install_ts_ms - first_ts) / 1000.0, 0)
        recency = max((install_ts_ms - last_ts) / 1000.0, 0)
        window = max((last_ts - first_ts) / 1000.0, 0)

        result['latency'] = latency
        result['recency'] = recency
        result['touch_window'] = window

        latency_hours = latency / 3600.0
        latency_days = latency / 86400.0
        window_hours = window / 3600.0

        result['touch_per_latency_hour'] = n / max(latency_hours, 1.0)
        result['touch_per_latency_day'] = n / max(latency_days, 1.0)
        result['touch_per_window_hour'] = n / max(window_hours, 1.0)
        result['recent_touch_pressure'] = (last1h_count / max(n, 1)) * (n / max(latency_hours, 1))
        result['recent_24h_ratio'] = last24h_count / max(n, 1)
        before_24h = n - last24h_count
        result['recent_24h_multiple'] = last24h_count / max(before_24h, 1)

    if n > 0:
        result['touch_count_ratio_0_30m'] = last30min_count / n
        result['touch_count_ratio_30m_1h'] = (last1h_count - last30min_count) / n
        result['touch_count_ratio_0_1h'] = last1h_count / n
        result['touch_count_ratio_1h_3h'] = (last3h_count - last1h_count) / n

    result['touchpoint_sequence'] = json.dumps(sequence, ensure_ascii=False)
    return result
```

### 5-4. Install Time Bin 생성

```python
import pandas as pd

def compute_install_time_bins(install_ts) -> dict:
    hour = pd.to_datetime(install_ts).hour
    return {
        'is_installed_02_06': 1 if 2 <= hour < 6 else 0,
        'is_installed_06_10': 1 if 6 <= hour < 10 else 0,
        'is_installed_10_14': 1 if 10 <= hour < 14 else 0,
        'is_installed_14_18': 1 if 14 <= hour < 18 else 0,
        'is_installed_18_22': 1 if 18 <= hour < 22 else 0,
        'is_installed_22_02': 1 if hour >= 22 or hour < 2 else 0,
    }
```

### 5-5. 키워드 분류

```python
def classify_keywords(sa_term_list, config_path: str = None) -> dict:
    """
    앱별로 keyword_classification을 커스터마이즈.
    config_path가 주어지면 해당 config에서 키워드 로드.
    """
    BRAND_KEYWORDS = []
    PRODUCT_KEYWORDS = []
    PROMO_KEYWORDS = ['할인', '세일', 'sale', '쿠폰', '특가', '블프']

    if config_path:
        with open(config_path) as f:
            config = json.load(f)
        kc = config.get('keyword_classification', {})
        BRAND_KEYWORDS = kc.get('brand_keywords', BRAND_KEYWORDS)
        PRODUCT_KEYWORDS = kc.get('product_keywords', PRODUCT_KEYWORDS)
        PROMO_KEYWORDS = kc.get('promo_keywords', PROMO_KEYWORDS)

    if isinstance(sa_term_list, str):
        try:
            sa_term_list = json.loads(sa_term_list)
        except:
            sa_term_list = []

    if not sa_term_list:
        return {
            'kw_brand_search': 0, 'kw_product_search': 0,
            'kw_promo_season_search': 0, 'keyword_list': '[]',
        }

    terms_lower = [t.lower() for t in sa_term_list if t]
    joined = ' '.join(terms_lower)

    return {
        'kw_brand_search': 1 if any(kw in joined for kw in BRAND_KEYWORDS) else 0,
        'kw_product_search': 1 if any(kw in joined for kw in PRODUCT_KEYWORDS) else 0,
        'kw_promo_season_search': 1 if any(kw in joined for kw in PROMO_KEYWORDS) else 0,
        'keyword_list': json.dumps(sa_term_list, ensure_ascii=False),
    }
```

### 5-6. 전체 파이프라인 함수

```python
import numpy as np

def process_weekly_data(df_sql: pd.DataFrame, config_path: str = None) -> pd.DataFrame:
    """
    SQL 결과 DataFrame -> 서비스 피처 형태 변환.
    config_path: 앱별 config JSON 경로 (없으면 기본값 사용)
    """
    df_sql['install_ts_ms'] = pd.to_datetime(df_sql['install_ts']).astype(np.int64) // 10**6

    records = []
    for _, row in df_sql.iterrows():
        rec = {}
        rec['app_id'] = row['app_id']
        rec['airbridge_uuid'] = row['airbridge_uuid']

        # Group A: Device (7)
        rec['OS_NAME'] = row.get('OS_NAME', '')
        rec['DEVICE_MANUFACTURER'] = row.get('DEVICE_MANUFACTURER', '')
        rec['DEVICE_LANGUAGE'] = row.get('DEVICE_LANGUAGE', '')
        rec['DEVICE_TIMEZONE'] = row.get('DEVICE_TIMEZONE', '')
        rec['DEVICE_OSVERSION'] = row.get('DEVICE_OSVERSION', '')
        rec['DEVICE_CARRIER'] = row.get('DEVICE_CARRIER', '')
        rec['IS_HAS_FRAUD'] = int(row.get('IS_HAS_FRAUD', 0))

        # Group B: Install Time (6)
        rec.update(compute_install_time_bins(row['install_ts']))

        # Group C: UA (47) -- Facebook 복원 후 계산
        journey = restore_facebook_touchpoints(
            row.get('journey_json', None),
            row.get('meta_touchpoint', None)
        )
        rec.update(parse_journey(journey, row['install_ts_ms']))

        # Keyword features
        rec.update(classify_keywords(row.get('sa_term_list', None), config_path))

        # Group D: InApp 5min (10)
        for col in ['product_viewed_count', 'user_signin', 'product_addedtocart',
                     'deeplink_open', 'home_viewed', 'addtowishlist', 'onboarding',
                     'user_signup', 'total_events', 'n_event_types']:
            rec[col] = int(row.get(col, 0) or 0)

        # Group F: Outcomes (3)
        rec['modal_clicked'] = int(row.get('modal_clicked', 0) or 0)
        rec['d3_purchase'] = int(row.get('d3_purchase', 0) or 0)
        rec['d3_churn'] = int(row.get('d3_churn', 0) or 0)

        records.append(rec)

    result = pd.DataFrame(records)

    # Fraud 유저 제거
    n_before = len(result)
    result = result[result['IS_HAS_FRAUD'] != 1].copy()
    print(f"Fraud filtering: {n_before} -> {len(result)} ({n_before - len(result)} removed)")

    return result
```

---

## 6. SDK 이벤트 스펙

### 6-1. `entry_modal_clicked` -- 모달 클릭 이벤트

| 항목 | 값 |
|------|-----|
| **이벤트 이름** | `entry_modal_clicked` |
| **Airbridge SDK 호출** | `Airbridge.trackEvent("entry_modal_clicked", ...)` |
| **Snowflake 위치** | `INTERNAL_MOBILE_EVENTS` |
| **필터** | `DATA__EVENTDATA__GOAL__CATEGORY = 'entry_modal_clicked'` |
| **필수 attribute** | 없음 (발생 여부만 사용) |
| **선택 attribute** | `trigger_type` (디버깅용) -- `DATA__EVENTDATA__GOAL__CUSTOMATTRIBUTES`에 JSON으로 저장 |

> **queryJ 검증**: `CUSTOMATTRIBUTES`는 JSON string. Snowflake에서 `PARSE_JSON()`으로 파싱.

**SDK 구현 예시 (iOS)**:
```swift
Airbridge.trackEvent("entry_modal_clicked")
```

**SDK 구현 예시 (Android)**:
```kotlin
Airbridge.trackEvent("entry_modal_clicked")
```

### 6-2. 데이터 저장 위치

| 데이터 | 저장 위치 | 이유 |
|--------|-----------|------|
| `assigned_trigger` | Supabase `prediction_logs` | API 호출 시점에 서버가 기록 |
| `is_random` | Supabase `prediction_logs` | 서버 내부 로직 |
| `modal_clicked` | **Airbridge SDK** | 클라이언트에서만 알 수 있는 정보 |

---

## 7. 데이터 수집 타이밍

### 7-1. 피처 가용 시점

| 데이터 | 가용 시점 |
|--------|-----------|
| Device 피처 | 설치 즉시 |
| UA features (journey) | 설치 후 ~1분 (FMT attribution 처리 지연) |
| InApp 5분 features | 설치 후 5분 |
| modal_clicked | 모달 클릭 직후 |
| d3_purchase | 설치 후 **3일** |
| d3_churn | 설치 후 **3일+** |

### 7-2. 주간 학습 데이터 시점 (D3 규칙)

```
오늘: 4월 2일 (수)

학습 대상 유저:
  설치 기간: 3월 23일 ~ 3월 29일 (지난주)
  -> D3 outcome: 3월 26일 ~ 4월 1일에 확정
  -> 4월 2일 시점에 모든 outcome 확정

이번 주 유저 (3월 30일 ~ 4월 2일):
  -> D3 outcome 아직 미확정
  -> 다음 주 학습에 포함
```

**규칙: 설치일 기준 3일 이상 경과한 유저만 학습에 포함.**

```python
from datetime import datetime, timedelta

today = datetime.now()
cutoff = today - timedelta(days=3)  # D3 = 최근 3일 제외

start_date = (today - timedelta(days=10)).strftime('%Y-%m-%d')
end_date = cutoff.strftime('%Y-%m-%d')
```

---

## 8. Supabase JOIN 로직

```python
# Supabase에서 prediction_logs 다운로드
# from supabase import create_client
# client = create_client(SUPABASE_URL, SUPABASE_KEY)
# logs = client.table("prediction_logs").select("*").eq("app_id", APP_ID).execute()
# df_logs = pd.DataFrame(logs.data)

# Snowflake 데이터와 JOIN
# df_merged = df_snowflake.merge(
#     df_logs[['airbridge_uuid', 'best_trigger', 'is_random']],
#     left_on='airbridge_uuid', right_on='airbridge_uuid',
#     how='left'
# )
# df_merged.rename(columns={'best_trigger': 'assigned_trigger'}, inplace=True)
```

---

## 9. 서버 변경 필요사항

25개 피처 -> ~70개 피처로 확장 시 서버 코드 변경이 필요하다. **아직 변경하지 말고, 데이터 파이프라인 검증 후 일괄 업데이트.**

### 9-1. 변경 필요 파일 목록

| 파일 | 현재 상태 | 변경 내용 |
|------|-----------|-----------|
| `server/predict.py` | `ALL_FEATURE_NAMES` = 25개 (UA 15 + InApp 10) | ~70개로 확장 |
| `server/feature_store.py` | `ALL_FEATURES` = 25개, `lookup()` returns shape (25,) | ~70개로 확장 |
| `data/feature_store.csv` | 25개 피처 컬럼 | ~70개 컬럼, categorical encoding 필요 |
| `models/{app_id}/*.pkl` | 25개 피처 기준 | **재학습 필수** |

### 9-2. predict.py 변경 상세

현재:
```python
UA_FEATURE_NAMES = [
    'trackinglink_count', 'DA_count', 'SA_count', 'unique_channel_count',
    'channel_entropy', 'last_touch_is_da', 'latency', 'recency',
    'recent_touch_pressure', 'touch_per_latency_hour', 'last1h_touch_count',
    'recent_24h_ratio', 'click_ratio', 'impression_count', 'is_single_touch_install',
]
INAPP_FEATURE_NAMES = [  # 10개 -- 변경 없음
    'product_viewed_count', 'user_signin', 'product_addedtocart',
    'deeplink_open', 'home_viewed', 'addtowishlist', 'onboarding',
    'user_signup', 'total_events', 'n_event_types',
]
```

변경 후:
```python
DEVICE_FEATURE_NAMES = [
    'OS_NAME_encoded', 'DEVICE_MANUFACTURER_encoded',
    'DEVICE_LANGUAGE_encoded', 'DEVICE_TIMEZONE_encoded',
    'DEVICE_OSVERSION_encoded', 'DEVICE_CARRIER_encoded',
    'IS_HAS_FRAUD',
]

INSTALL_TIME_FEATURE_NAMES = [
    'is_installed_02_06', 'is_installed_06_10', 'is_installed_10_14',
    'is_installed_14_18', 'is_installed_18_22', 'is_installed_22_02',
]

UA_FEATURE_NAMES = [
    # Binary (12 -- media_type은 별도 encoding)
    'has_touchpoint', 'has_last_touch',
    'last_touch_is_trackinglink', 'last_touch_is_da', 'last_touch_is_sa',
    'has_term', 'is_single_touch_install',
    'first_is_click', 'first_is_impression',
    'last_is_click', 'last_is_impression',
    'has_gm_touchpoint',
    # Temporal (9)
    'latency', 'recency', 'touch_window',
    'recent_touch_pressure', 'recent_24h_ratio', 'recent_24h_multiple',
    'touch_per_window_hour', 'touch_per_latency_day', 'touch_per_latency_hour',
    # Count (13)
    'DA_count', 'SA_count', 'trackinglink_count', 'total_touch_count',
    'unique_channel_count', 'click_count', 'impression_count', 'click_ratio',
    'term_total_count', 'term_unique_count',
    'last30min_touch_count', 'last1h_touch_count', 'last3h_touch_count',
    # Ratio (4)
    'touch_count_ratio_0_30m', 'touch_count_ratio_30m_1h',
    'touch_count_ratio_0_1h', 'touch_count_ratio_1h_3h',
    # Other (1)
    'channel_entropy',
    # Keyword (3)
    'kw_brand_search', 'kw_product_search', 'kw_promo_season_search',
]

INAPP_FEATURE_NAMES = [  # 10개 -- 변경 없음
    'product_viewed_count', 'user_signin', 'product_addedtocart',
    'deeplink_open', 'home_viewed', 'addtowishlist', 'onboarding',
    'user_signup', 'total_events', 'n_event_types',
]

ALL_FEATURE_NAMES = (DEVICE_FEATURE_NAMES + INSTALL_TIME_FEATURE_NAMES
                     + UA_FEATURE_NAMES + INAPP_FEATURE_NAMES)
```

### 9-3. 업데이트 순서 (권장)

```
1. 이 문서의 SQL 파이프라인으로 Snowflake 데이터 추출
2. Python process_weekly_data()로 ~75 컬럼 CSV 생성
3. 데이터 검증 -- 피처 분포, 결측률, fraud 비율
4. 모델 재학습 (LightGBM 권장)
5. predict.py, feature_store.py 피처 리스트 동기화
6. feature_store.csv 새 형식으로 교체
7. 모델 pkl 교체
8. 서버 재시작 + 통합 테스트
```

---

## 부록: 검증 이력

| 쿼리 | 검증 내용 | 파일 |
|------|-----------|------|
| query1 | SA 터치포인트에 `term` 필드 존재 확인 | `query_and_sample/query1.csv` |
| query2 | 터치포인트 JSON 키 전체 목록 (`ad_creative`, NOT `adcreative`) | `query_and_sample/query2.csv` |
| queryB | fraud type 분포 (0,1,2,3,4) | `query_and_sample/queryB.csv` |
| queryC2 | commerce app(30778) 이벤트 분포 | `query_and_sample/queryC2.csv` |
| queryD2 | 이벤트 카테고리 코드 매핑 (9360$$...) | `query_and_sample/queryD2.csv` |
| queryF | install=9161, open=9160 확인 | `query_and_sample/queryF.csv` |
| queryG2 | purchase에 `TOTALVALUE` 없음 (모두 NULL) | `query_and_sample/queryG2.csv` |
| queryI | 267,849 restricted 터치포인트 | `query_and_sample/queryI.csv` |
| queryJ | `CUSTOMATTRIBUTES`는 JSON string | `query_and_sample/queryJ.csv` |
| queryK | journey status 분포 | `query_and_sample/queryK.csv` |

---

*이 문서의 모든 컬럼명, 이벤트명, JSON 키는 실제 Snowflake 샘플 데이터에서 검증되었습니다.*
