# Airbridge Entry API — 운영 가이드

## 전체 구조

```
airbridge-entry-api-prototype/
├── server/                  # API 서버 코드 (Render에 배포)
│   ├── app.py               # FastAPI 앱 (엔드포인트 정의)
│   ├── predict.py            # 추론 로직 (모델 로드 + 예측)
│   ├── feature_store.py      # Feature Store (유저 feature lookup)
│   └── logger.py             # Supabase 로깅
├── notebooks/               # 운영 노트북 (주로 이걸 씀)
│   ├── onboarding.ipynb      # 새 앱 온보딩 (1회)
│   ├── weekly_training.ipynb # 매주 모델 재학습
│   └── cate_training.ipynb   # Phase 1→2 전환 시 CATE 학습 (1회)
├── scripts/
│   └── train_all_apps.py     # 전체 앱 배치 학습
├── configs/                 # 앱별 이벤트 매핑
│   ├── default_commerce.json # 기본 커머스 매핑 템플릿
│   └── {app_name}.json       # 앱별 매핑 (onboarding에서 생성)
├── data/                    # 학습 데이터
│   ├── feature_store.csv     # Feature Store (전체 앱 공용)
│   ├── {app_name}/           # 앱별 데이터 디렉토리
│   │   ├── weekly_2026-04-07.csv  # 매주 날짜별로 쌓임
│   │   ├── weekly_2026-04-14.csv  # 최신 파일을 자동으로 사용
│   │   └── rct_data.csv      # Phase 1 RCT 데이터 (1회)
│   ├── generate_feature_store.py  # 샘플 데이터 생성
│   └── generate_weekly_data.py    # 샘플 데이터 생성
├── models/                  # 학습된 모델 파일
│   └── {app_name}/
│       ├── d3_purchase_model.pkl  # D3 구매 예측
│       ├── d3_churn_model.pkl     # D3 이탈 예측
│       ├── cate_model.pkl         # Trigger CATE (없으면 exploration)
│       └── fa_params.json         # Factor Analysis 파라미터
├── docs/                    # 문서
├── Procfile                 # Render 배포 설정
├── requirements.txt         # Python 패키지
└── runtime.txt              # Python 버전
```

---

## 1. 새 앱 온보딩 (1회)

### 사전 준비물
- Airbridge 대시보드에서 앱의 `app_id` (숫자) 확인
- 서버에서 쓸 `app_name` 결정 (영문 소문자, 예: `athler`)
- Snowflake 접속 가능 상태

### Step 1: Snowflake에서 이벤트 목록 조회

```sql
SELECT DATA__EVENTDATA__GOAL__CATEGORY AS GOAL_CATEGORY, COUNT(*) AS CNT
FROM AIRBRIDGE.PUBLIC.INTERNAL_MOBILE_EVENTS
WHERE DATA__APP__APPID = {APP_ID}
AND DATA__EVENTDATA__CATEGORY LIKE '9360%'
GROUP BY 1 ORDER BY CNT DESC LIMIT 30;
```

### Step 2: 이벤트 목록 CSV 저장

결과를 `query_and_sample/events_{app_name}.csv`로 저장

### Step 3: 학습 데이터 추출 (과거 30~60일)

**온보딩 때는 넉넉하게 과거 데이터를 뽑습니다.** D3 Purchase/Churn 모델은 RCT와 무관하므로, 과거 데이터가 많을수록 모델이 정확해집니다.

```
온보딩 데이터 범위:
  start_date = 오늘 - 60일 (또는 30일)
  end_date = 오늘 - 3일 (D3 outcome 확정 필요)
```

SQL과 CSV 포맷은 `docs/weekly_data_format.md` 참고. 추출한 CSV를:
```
data/{app_name}/weekly_YYYY-MM-DD.csv
```
으로 저장. (예: `data/musinsa/weekly_2026-04-04.csv`)

**⚠️ 온보딩 데이터에는 `assigned_trigger`, `is_random`, `modal_clicked` 컬럼이 없어도 됩니다.**
이 컬럼들은 RCT 후 CATE 학습에만 쓰이고, D3 모델 학습에는 필요 없습니다.

### Step 4: onboarding.ipynb 실행

노트북 상단에서 설정:
```python
APP_ID = 30778       # Snowflake용 (숫자)
APP_NAME = "athler"  # 서버용 (문자열)
```

Step 1~9까지 순서대로 실행. 이벤트 매핑이 기본값 그대로면 10분, 수정 필요하면 30분.

### Step 4: Feature Store에 유저 추가

- **프로토타입**: `data/feature_store.csv`에 수동으로 유저 추가
- **실서비스**: Airbridge DB 연동 (엔지니어링팀 협의)

필요한 컬럼: `app_id`, `airbridge_uuid`, + 25개 feature

### Step 5: 고객사에 안내사항 전달

onboarding.ipynb Step 9 출력 내용을 복사하여 고객사 담당자에게 전달.
포함 내용: SDK 이벤트 태깅, entry_modal_clicked 코드, 모달 디자인, API 엔드포인트

### 완료 확인

```bash
# API 테스트
curl -X POST https://airbridge-entry-api-prototype.onrender.com/v1/entry/predict \
  -H "Content-Type: application/json" \
  -d '{"app_id": "athler", "airbridge_uuid": "test-user-001"}'

# 서버 상태 확인
curl https://airbridge-entry-api-prototype.onrender.com/health
```

---

## 2. 매주 모델 재학습

### 언제
매주 월요일

### 데이터 준비

**온보딩과 다른 점**: 매주 학습에서는 **Supabase prediction_logs와 JOIN**이 필요합니다.

```
매주 데이터 범위:
  start_date = 오늘 - 10일
  end_date = 오늘 - 3일 (D3 outcome 확정 필요)
  → 최근 7일간 설치 유저 (D3 outcome 확정된 것만)
```

#### 데이터 수집 흐름:

```
1. Snowflake에서 features + outcomes 추출 (최근 7일)
   → user_id, UA features(15), In-app features(10), d3_purchase, d3_churn

2. Supabase에서 prediction_logs 다운로드
   → user_id, assigned_trigger, is_random

3. user_id로 JOIN
   → Supabase에 없는 유저 (API 호출 전)은 assigned_trigger=NaN
   → D3 학습에는 전체 사용, CATE 학습에는 is_random=1만 사용

4. CSV로 저장:
   data/{app_name}/weekly_YYYY-MM-DD.csv
```

예: `data/musinsa/weekly_2026-04-07.csv`

**중요:**
- 노트북이 자동으로 가장 최신 `weekly_*.csv` 파일을 찾아 사용합니다
- 과거 데이터 파일은 삭제하지 마세요 (CATE 학습 시 누적 사용 가능)
- JOIN 방법 상세는 `docs/weekly_data_format.md` 참고

### 노트북 실행

`notebooks/weekly_training.ipynb` 열고 상단에서 앱 이름 변경:
```python
APP_NAME = "athler"  # onboarding.ipynb의 APP_NAME과 동일
```

Step 1~9 실행. 앱이 여러 개면 APP_NAME 바꿔가며 반복.

### 배치 실행 (앱이 여러 개일 때)

```bash
python scripts/train_all_apps.py
```

configs/ 폴더의 앱 목록을 자동 감지하여 전체 학습 + 업로드.

### AUC 기준

| 모델 | 최소 기준 | 실무 기준 |
|------|----------|----------|
| D3 Purchase | 0.65 | 0.75+ |
| D3 Churn | 0.60 | 0.65+ |

AUC가 기준 이하이면:
1. 데이터 확인 (이번 주 데이터가 정상인지)
2. Feature 분포 확인 (데이터 드리프트 여부)
3. 이전 모델 유지 (업로드하지 않음)

---

## 3. Phase 전환 (RCT → 최적화)

### 언제
랜덤 배정 유저가 500명 이상 쌓이면

### 확인 방법

Supabase에서 확인:
```sql
SELECT COUNT(*) FROM prediction_logs
WHERE app_id = 'athler' AND is_random = true;
```

### 실행

`notebooks/cate_training.ipynb` 열고:
```python
APP_NAME = "athler"
```

Step 1~7 실행. 또는 weekly_training.ipynb Step 6에서도 CATE 학습 가능.

### 결과

`cate_model.pkl` 서버 업로드 → 자동으로 exploration → optimized 모드 전환.
이후 80% 모델 추천 + 20% 랜덤 배정.

---

## 4. 주간 체크리스트

```
□ 각 앱 데이터 추출 (Snowflake → data/{app_name}/weekly_YYYY-MM-DD.csv)
□ weekly_training.ipynb 실행 (또는 python scripts/train_all_apps.py)
□ AUC 확인 (Purchase > 0.75, Churn > 0.65)
□ pkl 서버 업로드 완료 확인
□ API 테스트 (앱별 1건씩 curl)
□ Supabase 로그 확인 (새 로그가 쌓이고 있는지)
□ 모델 유저 CTR > 랜덤 유저 CTR 확인 (CATE 있는 앱만)
```

---

## 5. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 서버가 응답 안 함 | Render 인스턴스 sleep/crash | Render 대시보드 → Manual Deploy |
| 모든 유저가 404 | Feature Store에 유저 없음 | `data/feature_store.csv`에 유저 추가 |
| AUC가 갑자기 떨어짐 | 데이터 드리프트 | Snowflake 쿼리 확인, 이전 모델 유지 |
| Supabase 로그가 안 쌓임 | 환경변수 누락 | Render 환경변수 확인 (SUPABASE_URL, SUPABASE_KEY) |
| 모델 업로드 실패 | 서버 다운 or pkl 파일 손상 | 서버 health 확인, pkl 파일 크기 확인 |
| feature_store.csv 없음 경고 | 파일 삭제됨 | 서버는 빈 store로 시작, CSV 다시 생성 필요 |

---

## 6. 주요 설정값

| 항목 | 값 |
|------|-----|
| Render 서버 URL | `https://airbridge-entry-api-prototype.onrender.com` |
| Supabase | Render 환경변수의 `SUPABASE_URL`, `SUPABASE_KEY` |
| Snowflake | account, warehouse, database는 팀 내부 공유 |
| 모델 캐시 TTL | 1시간 (동일 유저 중복 요청 방지) |
| 랜덤 배정 비율 | optimized 모드에서 20% |
