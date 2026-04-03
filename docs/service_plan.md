# Airbridge Entry API — 서비스 스펙

## 한줄 요약

신규 유저가 커머스 앱을 열고 5분이 지나면, 광고 여정(UA) + 첫 5분 행동 데이터를 분석해서 **"어떤 trigger에 반응할지"** + **"D3 구매/이탈 확률"**을 예측하는 API.

---

## 1. 문제

- 커머스 앱 신규 유저 중 상당수가 첫 세션에서 전환 없이 이탈
- 지금은 모든 신규 유저에게 **똑같은 모달/배너**를 보여줌
- 유저마다 반응하는 자극이 다른데, 그걸 알 방법이 없음
- 신규 유저라서 in-app 히스토리도 없음 (cold-start)

## 2. 해결

Airbridge에 이미 쌓여있는 **UA 데이터** + 첫 5분 **in-app 이벤트**를 합쳐서:
1. 유저의 **성향** (latent dimensions)
2. 어떤 **trigger에 반응할지** (trigger scores)
3. 단기 **구매/이탈 확률** (pLTV)

를 API로 제공. 고객사는 이걸 받아서 맞춤 모달을 띄움.

**API 호출 가능 시점**: 유저 앱 오픈 후 **5분 이후**부터. (UA 데이터 도착 ~1분 + in-app 이벤트 축적 필요)

---

## 3. 전체 흐름: 처음부터 끝까지

아래가 고객사가 연동한 후 일어나는 전체 과정. **Phase별로 API가 자동으로 다르게 동작**하며, 고객사는 처음 연동 후 추가 작업 없음.

### Phase 0: 온보딩 (1~3주)

```
[우리가 하는 일]
1. 고객사의 기존 데이터(2~4주치)를 받아서 pLTV 모델 학습
   - 입력: UA features + in-app 이벤트
   - 출력: D3 구매 확률, D3 이탈 확률
   - 모델: Logistic Regression 또는 LightGBM (간단하게)
   - 고객사마다 따로 학습 (앱마다 유저 패턴이 다르므로)

2. Factor Analysis 모델 적용
   - UA 15개 feature → 6개 latent dimension으로 변환
   - 이건 범용 모델이라 고객사별 재학습 불필요

3. Feature Store 연동 확인
4. API 엔드포인트 준비

[고객사가 하는 일]
1. Trigger별 모달 4개 디자인/구현
2. API 연동 코드 개발
3. QA
```

### Phase 1: Exploration — RCT (4~9주)

**목적**: "어떤 유저가 어떤 trigger에 반응하는지" 데이터를 모으는 단계.

```
신규 유저 앱 오픈
    ↓
5분 경과
    ↓
고객사 서버 → API 호출
    ↓
API 내부 동작:
  1. Feature Store에서 이 유저의 UA + in-app 5분 데이터 조회
  2. Factor Analysis로 latent dimensions 계산
  3. pLTV 모델로 D3 구매/이탈 확률 계산
  4. Trigger는 ★랜덤 배정★ (5그룹 균등: Price/Social Proof/Scarcity/Novelty/Control)
    ↓
API 응답:
  {
    "mode": "exploration",
    "latent_dimensions": { ... },      ← 바로 제공
    "trigger_scores": null,            ← 아직 모델 없음
    "best_trigger": "social_proof",    ← 랜덤 배정된 것
    "pltv": { ... }                    ← 바로 제공
  }
    ↓
고객사 앱에서 best_trigger에 해당하는 모달 표시
    ↓
유저 반응 기록 (모달 클릭 여부, 상품 조회, 구매)
    ↓
★ 이 데이터가 쌓임: (UA features, in-app features, 배정된 trigger, 반응 여부) ★
```

**이 Phase에서 쌓이는 데이터 예시**:

```
유저A (즉시성 0.9, 채널다양성 0.2) → Price 배정 (랜덤) → 클릭 O, 구매 O
유저B (즉시성 0.3, 채널다양성 0.8) → Price 배정 (랜덤) → 클릭 X, 구매 X
유저C (즉시성 0.9, 채널다양성 0.3) → Novelty 배정 (랜덤) → 클릭 X, 구매 X
유저D (즉시성 0.3, 채널다양성 0.7) → Social Proof 배정 (랜덤) → 클릭 O, 구매 O
...
× 7,685명
```

랜덤 배정이라서 비슷한 유저가 서로 다른 trigger를 받게 됨. 이걸 비교하면 "어떤 유저에게 어떤 trigger가 효과적인지" 알 수 있음.

**필요 샘플**: 그룹당 ~1,537명 × 5그룹 = ~7,685명 (일 200명 기준 약 6주)

### Phase 2: 모델 학습 (10~11주)

**목적**: Phase 1에서 모은 RCT 데이터로 trigger 반응 예측 모델을 만드는 단계.

```
[우리가 하는 일]
1. ATE 분석: trigger 간 평균 효과 차이가 있는지 확인
   - "Price가 평균 클릭률 20%이고 Novelty가 12%이면 유의미한 차이"
   - 차이가 없으면 → trigger가 잘못 설계된 것, 재설계 필요

2. CATE 모델 학습 (Causal Forest)
   - 입력: 유저의 latent dimensions (6개) + in-app features (~10개)
   - 출력: 이 유저가 각 trigger에 반응할 확률
   - 학습 데이터: Phase 1에서 모은 RCT 데이터
   - 모델이 자동으로 패턴을 찾음:
     "즉시성 높고 프로모션 관심 높은 유저 → Price에 반응 확률 82%"
     "숙고형 + 다채널 유저 → Social Proof에 반응 확률 71%"

3. 모델 검증 후 API를 optimized 모드로 전환

[고객사가 하는 일]
- 없음. 결과 리포트만 받으면 됨. API 모드가 자동 전환.
```

### Phase 3: 운영 (12주~)

**목적**: 모델 추천을 쓰면서 일부 랜덤 배정을 유지하는 단계.

```
신규 유저 앱 오픈 → 5분 경과 → API 호출
    ↓
API 내부 동작:
  1. Feature Store에서 유저 데이터 조회
  2. CATE 모델이 trigger별 반응 확률 계산
  3. 배정:
     ┌──────────────────────────────────────┐
     │ 80%: 모델 추천 best trigger 배정     │
     │ 20%: 랜덤 배정 (RCT 데이터 계속 축적)│
     └──────────────────────────────────────┘
    ↓
API 응답:
  {
    "mode": "optimized",
    "trigger_scores": { ... },
    "best_trigger": "price_appeal",
    "pltv": { ... }
  }
```

**20% 랜덤을 유지하는 이유**: 계절/유저풀/캠페인 변화에 대한 데이터를 계속 모으기 위함.

**모델 재학습**: 수동. 데이터 충분히 쌓이면 우리가 판단해서 재학습 (자동화 불필요).

---

## 4. 4가지 Trigger

커머스 보편적으로 쓸 수 있는 4개 trigger. 각각 서로 다른 심리적 메커니즘을 자극. 우리가 정하는 건 **trigger 유형**뿐, 구체적 멘트/디자인은 고객사가 결정.

| Trigger | 자극하는 것 | 이론적 근거 | 고객사 멘트 예시 |
|---|---|---|---|
| **Price Appeal** | 경제적 이득감 | Transaction Utility (Thaler 1985) | "첫 구매 20% 할인", "최대 70% OFF" |
| **Social Proof** | 남들 따라하기 | Principles of Persuasion (Cialdini 1984) | "1,234명이 구매", "인기 랭킹 TOP 10" |
| **Scarcity** | 놓치면 손해 | Loss Aversion (Cialdini 1984; Worchel 1975) | "3개 남음", "오늘 자정 종료" |
| **Novelty** | 새로운 거 보고 싶다 | Novelty Seeking (Hirschman 1980) | "이번 주 신상품", "트렌드 아이템" |

**왜 이 4개인가**: Price → 돈 / Social Proof → 남들 / Scarcity → 시간 / Novelty → 새로움. 서로 다른 심리적 메커니즘이고, 어떤 커머스 앱이든 구현 가능.

---

## 5. Input 데이터

### 5-1. UA Features (광고 여정, 앱 오픈 전)

Airbridge DB에서 자동 조회. 15개 feature 사용.

| 그룹 | Feature | Importance | 설명 |
|---|---|---|---|
| 채널 | `trackinglink_count` | 12.1% (1위) | 트래킹 링크 접점 수 |
| | `DA_count` | 2.2% | 디스플레이 광고 접점 수 |
| | `SA_count` | - | 검색 광고 접점 수 |
| | `unique_channel_count` | 1.7% | 채널 다양성 |
| | `channel_entropy` | 2.4% | 채널 분산도 |
| | `last_touch_is_da` | 1.1% | 마지막 접점이 DA인지 |
| 시간 | `latency` | 8.1% | 첫 접점~설치 기간 |
| | `recency` | 7.9% | 마지막 접점~설치 간격 |
| | `recent_touch_pressure` | 6.9% | 최근 접점 밀도 |
| | `touch_per_latency_hour` | 4.5% | 시간당 접점 빈도 |
| | `last1h_touch_count` | 6.4% | 최근 1시간 접점 수 |
| | `recent_24h_ratio` | 1.5% | 최근 24시간 집중도 |
| 행동 | `click_ratio` | 1.5% | 클릭/노출 비율 |
| | `impression_count` | 0.5% | 노출 수 |
| | `is_single_touch_install` | - | 단일 터치 설치 여부 |

**Organic 유저(~6%)**: UA feature가 전부 0. in-app 데이터만으로 예측 (Athler 기준 AUC 0.790).

### 5-2. In-app Features (첫 5분 행동)

SDK에서 자동 수집. API 호출 시점(5분)까지 쌓인 이벤트를 집계.

| Feature | 발생 유저 비율 | D3 구매 상관 | 설명 |
|---|---|---|---|
| `product.viewed` (건수) | 66.5% | **+0.257** | 상품 조회 수 (가장 강력) |
| `user.signin` | 67.9% | **+0.234** | 로그인 여부 |
| `product.addedtocart` | 11.8% | **+0.193** | 장바구니 담기 |
| `deeplink_open` | 12.6% | +0.137 | 딥링크 유입 |
| `home.viewed` | 38.2% | +0.082 | 홈 화면 탐색 |
| `addtowishlist` | 5.5% | +0.025 | 위시리스트 |
| `onboarding` | 16.0% | -0.142 | 온보딩 진행 중 |
| `user.signup` | 11.3% | -0.103 | 신규 가입 |
| `total_events` | - | - | 총 이벤트 수 |
| `n_event_types` | - | - | 이벤트 종류 수 |

**Leakage 제외**: `order.completed`, `order.canceled`, `initiatecheckout` (구매 자체이므로 예측 변수로 사용 불가)

### 5-3. 검증된 예측 성능 (Athler 기준, D7 Purchase AUC)

| 데이터 조합 | RF AUC | 의미 |
|---|---|---|
| Device만 | 0.537 | 거의 동전 던지기 |
| UA만 | **0.694** | UA의 독립적 가치 |
| In-app 10분만 | **0.765** | 10분 행동이 더 강력 |
| **UA + In-app 10분** | **0.781** | **보완재 확인 (결합 > 개별 최대)** |

---

## 6. 모델링 상세

### 6-1. 전체 파이프라인

```
유저 앱 오픈 → 5분 경과 → API 호출
    ↓
Feature Store에서 데이터 조회:
  UA 15개 feature + In-app 5분 ~10개 feature
    ↓
[모델 1] Factor Analysis
  UA 15개 feature → 6개 latent dimension (연속 스코어)
  방법: Varimax rotation, 사전 학습된 loading matrix 적용
  고객사별 재학습 불필요 (범용)
    ↓
[모델 2] Trigger 반응 예측 (CATE)
  입력: latent dimensions 6개 + in-app features ~10개
  출력: trigger별 반응 확률 4개
  방법: Causal Forest (Athey & Imbens 2016)
  고객사별 학습 필요 (RCT 데이터 기반)
  ※ Phase 1에서는 이 모델이 없으므로 랜덤 배정
    ↓
[모델 3] pLTV 예측
  입력: UA 15개 + in-app ~10개 (전체 ~25개 feature)
  출력: D3 구매 확률, D3 이탈 확률
  방법: Logistic Regression 또는 LightGBM
  고객사별 학습 필요 (기존 데이터 2~4주치로 학습)
    ↓
API Response 조립
```

### 6-2. 모델 1: Latent Dimension 추출

**무엇을 하는 모델인가**: UA 15개 feature를 6개 핵심 차원으로 압축. "이 유저의 광고 여정이 어떤 성격인지"를 요약.

**방법**: Factor Analysis (Varimax rotation)
**입력**: UA 15개 feature (z-score standardized)
**출력**: 6개 스코어 (유저마다 다른 연속값)

| Factor | 이름 | 핵심 feature (loading) | 분산 설명 | D3 구매 상관 |
|---|---|---|---|---|
| F1 | 광고 강도 | trackinglink_count (0.96), touch_pressure (0.95) | 16.7% | r=+0.091 |
| F2 | DA 채널 | DA_count (0.92), last_touch_is_da (0.40) | 7.9% | 유의미하지 않음 |
| F3 | 수동 노출 | impression_count (0.97), click_ratio (-0.69) | 9.8% | r=-0.057 |
| F4 | 채널 다양성 | channel_entropy (-0.91), single_touch (+0.66) | 11.7% | **r=-0.144 (가장 강함)** |
| F5 | 시간 집중도 | recent_24h_ratio (-0.82), touch_per_hour (-0.63) | 10.0% | r=-0.097 |
| F6 | 최근성 | recency (+0.56) | 3.2% | r=-0.034 |

**고객사별 재학습 필요 없음** — loading matrix는 범용적. 새 유저가 오면 기존 matrix에 feature를 넣어서 스코어만 계산.

### 6-3. 모델 2: Trigger 반응 예측 (CATE)

**무엇을 하는 모델인가**: "이 유저에게 Price trigger를 보여주면 클릭할 확률은 82%이고, Social Proof를 보여주면 45%이다"를 예측.

**방법**: Causal Forest (Athey & Imbens 2016)
**입력**: latent dimensions 6개 + in-app features ~10개 = ~16개 feature
**출력**: 4개 trigger 각각의 반응 확률

**학습 과정**:
```
RCT 데이터 (Phase 1에서 수집):
  유저A (features) → Price 배정 → 클릭 O
  유저B (features) → Price 배정 → 클릭 X
  유저C (features) → Social Proof 배정 → 클릭 O
  ...

Causal Forest가 학습하는 것:
  "features가 이런 패턴일 때 Price의 효과는 +15%p이고
   Social Proof의 효과는 +3%p이다"
  → 이 유저에게는 Price가 best trigger
```

**고객사별 학습 필요** — RCT 데이터가 고객사마다 다르므로.

**Phase 1에서는 이 모델이 없음** → trigger를 랜덤 배정 (이게 RCT).
**Phase 2에서 학습** → Phase 3부터 예측 제공.

### 6-4. 모델 3: pLTV 예측

**무엇을 하는 모델인가**: "이 유저가 3일 내 구매할 확률은 72%이다"를 예측.

**방법**: Logistic Regression 또는 LightGBM (간단한 모델로 충분)
**입력**: UA 15개 + in-app ~10개 = ~25개 feature
**출력**: D3 구매 확률, D3 이탈 확률

**고객사별 학습 필요** — 앱마다 유저 행동 패턴이 다르므로.
- 온보딩 시 고객사 기존 데이터(2~4주치)로 초기 모델 학습
- 이후 주 1회 재학습 (새 데이터 반영)
- 참고 성능 (Athler 기준): D3 Purchase AUC 0.864, D3 Churn AUC 0.743

**RCT 불필요** — 기존 observational 데이터로 학습 가능.

---

## 7. API 스펙

### 7-1. Endpoint

```
POST /v1/entry/predict
```

### 7-2. Request

```json
{
  "user_id": "abc123"
}
```

user_id만 보내면 됨. UA/in-app 데이터는 Airbridge 내부에서 자동 조회.

**호출 타이밍**: 유저 앱 오픈 후 **5분 이후**.

### 7-3. Response

```json
{
  "user_id": "abc123",
  "mode": "optimized",
  "latent_dimensions": {
    "ad_intensity": 0.85,
    "display_ad": 0.12,
    "passive_exposure": 0.23,
    "channel_diversity": 0.72,
    "time_concentration": 0.91,
    "recency": 0.65
  },
  "trigger_scores": {
    "price_appeal": 0.82,
    "social_proof": 0.45,
    "scarcity": 0.38,
    "novelty": 0.31
  },
  "best_trigger": "price_appeal",
  "pltv": {
    "d3_purchase_prob": 0.72,
    "d3_churn_prob": 0.21
  }
}
```

### 7-4. 필드 설명

| 필드 | 타입 | 설명 |
|---|---|---|
| `mode` | string | `"exploration"` (랜덤 배정) / `"optimized"` (모델 추천 80% + 랜덤 20%) |
| `latent_dimensions` | object | 6개 UA 기반 유저 성향 스코어 (0~1) |
| `trigger_scores` | object | 4개 trigger별 반응 확률 (0~1). exploration에서는 null |
| `best_trigger` | string | 추천 trigger (exploration에서는 랜덤 배정) |
| `pltv.d3_purchase_prob` | float | 3일 내 구매 확률 (0~1) |
| `pltv.d3_churn_prob` | float | 3일 내 이탈 확률 (0~1) |

### 7-5. Phase별 API 응답 차이

| 필드 | Phase 1 (Exploration) | Phase 3 (Optimized) |
|---|---|---|
| `mode` | `"exploration"` | `"optimized"` |
| `latent_dimensions` | 제공 | 제공 |
| `trigger_scores` | **null** | 제공 |
| `best_trigger` | **100% 랜덤 배정** | 80% 모델 추천 + 20% 랜덤 |
| `pltv` | 제공 | 제공 |

### 7-6. 고객사 활용 시나리오

```
Case 1: 고가치 + Price trigger
  d3_purchase_prob = 0.72, best_trigger = "price_appeal"
  → 공격적 할인 쿠폰 모달 (투자 가치 있음)

Case 2: 저가치 + Social Proof
  d3_purchase_prob = 0.15, best_trigger = "social_proof"
  → 인기 상품 랭킹 모달 (쿠폰 아낌)

Case 3: 이탈 위험 + Scarcity
  d3_churn_prob = 0.85, best_trigger = "scarcity"
  → 긴급 모달로 이탈 방지

Case 4: Organic 유저 (UA 없음)
  latent_dimensions = all 0
  → in-app 행동 기반으로만 예측
```

### 7-7. 에러 처리

| 상황 | 응답 |
|---|---|
| user_id 없음 | 400 Bad Request |
| 유저 데이터 없음 | 404 Not Found |
| UA 미도착 | latent_dimensions = null, in-app만으로 예측 |
| in-app 이벤트 0건 | UA만으로 예측, 정확도 낮음 경고 |
| CATE 모델 미학습 (Phase 1) | trigger_scores = null, best_trigger = 랜덤 |

---

## 8. RCT 설계

### 8-1. 목적

Trigger 반응 예측 모델(CATE, 모델 2) 학습에 필요한 데이터 수집.

### 8-2. 실험 그룹

| 그룹 | 내용 | 역할 |
|---|---|---|
| T1 | Price Appeal 모달 | Treatment |
| T2 | Social Proof 모달 | Treatment |
| T3 | Scarcity 모달 | Treatment |
| T4 | Novelty 모달 | Treatment |
| C | 기존 경험 (현재 모달 또는 없음) | Control |

### 8-3. Outcome

| Outcome | 측정 시점 | 역할 |
|---|---|---|
| **모달 클릭 여부** | 즉시 | Primary |
| **첫 세션 상품 조회 수** | 첫 세션 | Secondary |
| **첫 세션 구매 여부** | 첫 세션 | Secondary |
| D3 구매 / D3 재방문 | 7일 후 | Robustness check |

### 8-4. 샘플 사이즈

가정: baseline 클릭률 15%, MDE 5%p, α=0.05, power=0.80, Bonferroni 보정

| 단계 | 그룹당 | 총 (5그룹) | 일 200명 기준 | 일 500명 기준 |
|---|---|---|---|---|
| **ATE 검증** | 1,537명 | **7,685명** | **39일 (~6주)** | 16일 |
| CATE 추정 | 4,611명 | 23,055명 | 116일 (~4개월) | 47일 |

### 8-5. RCT에서 수집되는 데이터 형태

유저 1건:

```json
{
  "user_id": "abc123",
  "ua_features": {
    "trackinglink_count": 3,
    "recency": 120,
    "click_ratio": 0.6,
    ...
  },
  "latent_dimensions": {
    "ad_intensity": 0.85,
    "channel_diversity": 0.72,
    ...
  },
  "inapp_features": {
    "product_viewed_count": 5,
    "user_signin": 1,
    "total_events": 12,
    ...
  },
  "assigned_trigger": "price_appeal",
  "outcomes": {
    "modal_clicked": true,
    "first_session_product_views": 8,
    "first_session_purchase": false
  }
}
```

---

## 9. 시스템 구조

### 9-1. 전체 구조: 로컬(오프라인) + 서버(온라인)

```
┌─────────────────────────────────────────────┐
│            로컬 (노트북)                      │
│                                              │
│  Airbridge DB → 데이터 다운로드               │
│       ↓                                      │
│  노트북에서 모델 학습                          │
│       ↓                                      │
│  파라미터 파일 생성:                           │
│    · fa_params.json    (FA loading matrix)   │
│    · pltv_model.pkl    (pLTV 모델)           │
│    · churn_model.pkl   (Churn 모델)          │
│    · cate_model.pkl    (CATE 모델, Phase 2~) │
│       ↓                                      │
│  서버에 파라미터 파일 업로드                    │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│            서버 (온라인) — inference만         │
│                                              │
│  ┌───────────┐  ┌────────────┐              │
│  │ Feature   │  │ 파라미터    │              │
│  │ Store     │  │ 파일들     │              │
│  │ (UA+InApp)│  │ (.json/.pkl)│              │
│  └─────┬─────┘  └─────┬──────┘              │
│        │               │                     │
│        └───────┬───────┘                     │
│                ▼                              │
│  ┌──────────────────────┐                    │
│  │ API Server           │                    │
│  │ (inference + 분기)    │                    │
│  └──────────┬───────────┘                    │
│             ▼                                │
│       API 응답 리턴                           │
└─────────────────────────────────────────────┘
              ▲
              │
    고객사 서버 → POST /v1/entry/predict
```

### 9-2. 파라미터 파일

| 파일 | 내용 | 크기 | 업데이트 주기 |
|---|---|---|---|
| `fa_params.json` | loading matrix (15×6), mean/std (정규화용) | ~2KB | 거의 안 바뀜 |
| `pltv_model.pkl` | D3 Purchase 예측 모델 (LightGBM) | ~1MB | 주 1회 |
| `churn_model.pkl` | D3 Churn 예측 모델 (LightGBM) | ~1MB | 주 1회 |
| `cate_model.pkl` | Trigger 반응 예측 모델 (Causal Forest) | ~5MB | 수동 (데이터 쌓이면) |

### 9-3. 로컬에서 하는 일 (노트북)

```
[초기 셋업 — 1회]
1. FA 학습: UA features → loading matrix 추출 → fa_params.json 저장
2. pLTV 학습: 고객사 기존 데이터로 LightGBM fit → pltv_model.pkl 저장
3. Churn 학습: 동일 → churn_model.pkl 저장
4. 파라미터 파일 서버에 업로드

[주 1회 — pLTV/Churn 재학습]
1. Airbridge DB에서 최근 데이터 다운로드
2. pLTV 모델 재학습 → pltv_model.pkl 교체
3. Churn 모델 재학습 → churn_model.pkl 교체
4. 서버에 업로드

[Phase 2 — CATE 모델 학습 (1회)]
1. RCT 데이터 다운로드 (Phase 1에서 모은 것)
2. ATE 분석 (trigger 간 효과 차이 확인)
3. Causal Forest 학습 → cate_model.pkl 저장
4. 서버에 업로드 → 서버가 자동으로 optimized 모드로 전환

[이후 필요시 — CATE 재학습]
1. 20% 랜덤 배정 데이터가 충분히 쌓였을 때
2. 판단해서 수동으로 재학습
```

### 9-4. 서버에서 하는 일 (API Server)

**서버에는 학습 로직이 전혀 없음. 파라미터 파일 로드 → inference → 응답만.**

```python
# 서버 시작 시 파라미터 로드
fa_params = load_json("fa_params.json")        # loading matrix, mean, std
pltv_model = load_pkl("pltv_model.pkl")        # D3 purchase 모델
churn_model = load_pkl("churn_model.pkl")      # D3 churn 모델
cate_model = load_pkl("cate_model.pkl")        # 없으면 None (Phase 1)

def predict(user_id):
    # 1. Feature Store에서 데이터 가져오기
    ua = feature_store.get_ua(user_id)          # 15개 feature
    inapp = feature_store.get_inapp(user_id)    # 10개 feature

    # 2. FA: latent dimensions (행렬 곱 한 번)
    ua_norm = (ua - fa_params["mean"]) / fa_params["std"]
    latent_dims = ua_norm @ fa_params["loading_matrix"]   # 15 → 6차원

    # 3. Trigger 배정
    if cate_model is None:
        # Phase 1: CATE 모델 없음 → 100% 랜덤
        mode = "exploration"
        trigger_scores = None
        best_trigger = random_choice(["price", "social_proof",
                                       "scarcity", "novelty", "control"])
    else:
        # Phase 3: CATE 모델 있음
        mode = "optimized"
        features = concat(latent_dims, inapp)
        trigger_scores = cate_model.predict(features)  # 4개 확률

        if random() < 0.2:
            # 20% 랜덤 (RCT 데이터 계속 축적)
            best_trigger = random_choice(["price", "social_proof",
                                           "scarcity", "novelty"])
        else:
            # 80% 모델 추천
            best_trigger = argmax(trigger_scores)

    # 4. pLTV
    all_features = concat(ua, inapp)
    d3_purchase = pltv_model.predict_proba(all_features)
    d3_churn = churn_model.predict_proba(all_features)

    # 5. 응답
    return {
        "user_id": user_id,
        "mode": mode,
        "latent_dimensions": latent_dims,
        "trigger_scores": trigger_scores,
        "best_trigger": best_trigger,
        "pltv": {
            "d3_purchase_prob": d3_purchase,
            "d3_churn_prob": d3_churn
        }
    }
```

**모드 전환 로직**: `cate_model.pkl` 파일이 있으면 `"optimized"`, 없으면 `"exploration"`. 파일 업로드만으로 전환.

### 9-5. 컴포넌트

| 컴포넌트 | 역할 | 비고 |
|---|---|---|
| **Feature Store** | UA(DB) + in-app(실시간)을 유저별로 집계/저장 | 핵심 개발 |
| **API Server** | 파라미터 로드 → inference → 응답 | 학습 로직 없음, 심플 |
| **파라미터 파일 저장소** | .json/.pkl 파일 관리 | S3 등 |
| **Outcome Tracker** | 모달 클릭/구매 이벤트 수집 (Airbridge SDK) | 기존 인프라 활용 |

---

## 10. 고객사 연동

### 10-1. 고객사가 준비할 것

1. **모달 4개 구현** (trigger별)
   - Price Appeal: 할인/쿠폰 강조
   - Social Proof: 인기/랭킹 강조
   - Scarcity: 한정/긴급성 강조
   - Novelty: 신상품/트렌드 강조

2. **API 연동 코드** (앱 서버)
   ```
   유저 앱 오픈 → 5분 대기 (또는 특정 이벤트 트리거) →
   POST /v1/entry/predict { "user_id": "..." } →
   response.best_trigger에 따라 모달 분기
   ```

3. **Outcome 이벤트**: Airbridge SDK 이미 쓰고 있으면 추가 작업 없음

### 10-2. 타임라인

| 주차 | 고객사 | 우리 |
|---|---|---|
| 1~3주 | 모달 4개 디자인/개발, API 연동 | Feature Store + API 준비, pLTV 모델 학습 |
| 4~9주 | - | RCT 데이터 수집 (exploration mode) |
| 10~11주 | 1차 결과 리포트 확인 | ATE 분석 + CATE 모델 학습 |
| 12주~ | - | 최적화 모드 자동 전환 |

---

## 11. 역할 분담

| 우리 (Airbridge) | 고객사 |
|---|---|
| UA + in-app 데이터 파이프라인 | Trigger별 모달 4개 구현 |
| Feature Store 구축/운영 | 구체적 멘트/카피 작성 |
| 3개 모델 학습/서빙 (FA, CATE, pLTV) | API 호출 → 모달 분기 코드 |
| RCT 운영 (20% 랜덤 유지) | (Phase 1 이후 할 일 없음) |
| 필요시 수동 모델 재학습 | |
| 성과 대시보드 | 대시보드 확인 |

---

## 12. MVP 범위

### MVP (~3개월)

- [ ] Feature Store: UA 15개 + In-app 5분 10개
- [ ] 모델 1 (FA): 6개 latent dimension 제공
- [ ] 모델 3 (pLTV): 고객사 기존 데이터로 학습, D3 구매/이탈 예측
- [ ] API: latent_dimensions + pltv + best_trigger(랜덤) 리턴
- [ ] RCT: trigger 랜덤 배정 + outcome 수집
- [ ] 파트너 1곳

### V1 (~6개월)

- [ ] 모델 2 (CATE): RCT 데이터 기반 trigger 반응 예측
- [ ] API: trigger_scores + 모델 기반 best_trigger 추가 (80% 추천 + 20% 랜덤)
- [ ] 필요시 수동 모델 재학습
- [ ] 성과 대시보드

### V2 (확장)

- [ ] 파트너 N곳
- [ ] Cross-app 모델 (앱 A 데이터 → 앱 B cold-start 적용)
- [ ] 고객사 커스텀 trigger 추가 가능
- [ ] 실시간 A/B 테스트 기능

---

## 13. 세일즈 피치

> **"지금 모든 신규 유저에게 똑같은 모달 보여주시죠?"**
>
> 저희 API 하나만 연동하면:
> 1. 유저마다 **가장 반응할 trigger를 자동 추천** → 모달 클릭률 향상
> 2. **D3 구매/이탈 확률** 제공 → 쿠폰 예산 최적화
> 3. 6주 후부터 **자동 최적화** — 이후 할 일 없음
>
> Airbridge SDK 이미 쓰고 계시니까 **추가 데이터 수집 없이** 바로 가능합니다.
