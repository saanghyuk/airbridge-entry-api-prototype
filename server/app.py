"""
Airbridge Entry API Server

멀티앱 지원: 앱별로 모델이 분리되어 있고, 최초 요청 시 lazy loading.

실행: uvicorn server.app:app --reload
테스트: http://localhost:8000/docs (Swagger UI에서 바로 테스트 가능)
"""
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
from server.predict import load_models_for_app, reload_models_for_app, predict, get_loaded_apps, list_available_apps, MODEL_DIR
from server.feature_store import FeatureStore
from server.logger import log_prediction

# Feature Store만 시작 시 로드 (모델은 앱별 lazy loading)
store = FeatureStore()

app = FastAPI(
    title="Airbridge Entry API",
    description="멀티앱 지원. 신규 유저의 trigger 추천 + D3 구매/이탈 예측. 앱별로 모델이 분리되어 있고, 최초 요청 시 자동 로드.",
)


class PredictRequest(BaseModel):
    app_id: str
    airbridge_uuid: str

    class Config:
        json_schema_extra = {
            "example": {
                "app_id": "ablog",
                "airbridge_uuid": "21d7d787-93cd-466b-a582-6970e9512e99",
            }
        }


@app.post("/v1/entry/predict")
def entry_predict(req: PredictRequest, background_tasks: BackgroundTasks):
    """
    신규 유저의 trigger 추천 + D3 구매/이탈 예측.

    클라이언트는 app_id + airbridge_uuid만 전송.
    서버가 앱별 모델을 로드하고, Feature Store에서 피처를 조회하여 inference 수행.
    """
    # 1. 앱별 모델 로드 (캐시되어 있으면 즉시 반환)
    models = load_models_for_app(req.app_id)
    if models is None:
        raise HTTPException(
            status_code=404,
            detail=f"App not found: {req.app_id}"
        )

    # 2. Feature Store에서 유저 피처 조회
    features = store.lookup(req.app_id, req.airbridge_uuid)
    if features is None:
        raise HTTPException(
            status_code=404,
            detail=f"User not found: app_id={req.app_id}, uuid={req.airbridge_uuid}"
        )

    # 3. 예측
    result = predict(req.app_id, req.airbridge_uuid, features, models)

    # 4. 예측 결과 로깅 — 응답 반환 후 백그라운드에서 실행 (레이턴시 영향 없음)
    background_tasks.add_task(log_prediction, req.app_id, result)

    return result


@app.get("/health")
def health():
    """서버 상태 확인 — 사용 가능한 앱 목록 + 로드된 앱 상태"""
    available = list_available_apps()
    loaded = get_loaded_apps()
    return {
        "status": "ok",
        "feature_store_users": store.user_count,
        "available_apps": available,
        "loaded_apps": loaded,
    }


VALID_MODEL_FILES = {
    "fa_params.json",
    "d3_purchase_model.pkl",
    "d3_churn_model.pkl",
    "cate_model.pkl",
    "pltv_purchase_model.pkl",
    "pltv_amount_model.pkl",
    "pltv_tier_config.json",
}


@app.post("/v1/models/{app_id}/upload")
async def upload_model(app_id: str, file: UploadFile = File(...)):
    """
    앱별 모델 파일 업로드. 업로드 후 자동으로 모델 리로드.

    허용 파일: fa_params.json, d3_purchase_model.pkl, d3_churn_model.pkl, cate_model.pkl
    """
    if file.filename not in VALID_MODEL_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file: {file.filename}. Allowed: {VALID_MODEL_FILES}"
        )

    # 앱 디렉토리 생성 (새 앱이면 자동 생성)
    app_dir = MODEL_DIR / app_id
    app_dir.mkdir(parents=True, exist_ok=True)

    # 파일 저장
    file_path = app_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 모델 리로드 시도 (필수 파일 2개 다 있어야 성공)
    models = reload_models_for_app(app_id)

    if models:
        mode = "optimized" if models.get("cate") else "exploration"
        message = f"Model uploaded and reloaded for {app_id}"
    else:
        # 아직 필수 파일이 덜 올라옴
        app_dir = MODEL_DIR / app_id
        required = ["d3_purchase_model.pkl", "d3_churn_model.pkl"]
        missing = [f for f in required if not (app_dir / f).exists()]
        mode = "not ready"
        message = f"File saved. Still missing: {missing}"

    return {
        "status": "ok",
        "app_id": app_id,
        "file": file.filename,
        "size_kb": round(len(content) / 1024, 1),
        "mode": mode,
        "message": message,
    }


@app.delete("/v1/models/{app_id}/{filename}")
def delete_model(app_id: str, filename: str):
    """
    앱의 특정 모델 파일 삭제. 예: cate_model.pkl 삭제하면 exploration 모드로 전환.
    """
    if filename not in VALID_MODEL_FILES:
        raise HTTPException(400, f"Invalid file: {filename}")

    file_path = MODEL_DIR / app_id / filename
    if not file_path.exists():
        raise HTTPException(404, f"File not found: {app_id}/{filename}")

    file_path.unlink()
    models = reload_models_for_app(app_id)

    mode = "optimized" if models and models.get("cate") else "exploration"
    return {
        "status": "ok",
        "app_id": app_id,
        "deleted": filename,
        "mode": mode,
    }


@app.get("/v1/models/{app_id}")
def list_models(app_id: str):
    """앱에 업로드된 모델 파일 목록 조회"""
    app_dir = MODEL_DIR / app_id
    if not app_dir.exists():
        raise HTTPException(404, f"App not found: {app_id}")

    files = {}
    for f in sorted(app_dir.iterdir()):
        if f.is_file():
            files[f.name] = {"size_kb": round(f.stat().st_size / 1024, 1)}

    loaded = get_loaded_apps()
    mode = loaded.get(app_id, "not loaded")

    return {
        "app_id": app_id,
        "mode": mode,
        "files": files,
    }


@app.get("/v1/users/{app_id}")
def list_users(app_id: str):
    """테스트 편의를 위한 유저 UUID 목록 조회"""
    uuids = store.list_users(app_id)
    if not uuids:
        raise HTTPException(status_code=404, detail=f"No users found for app_id={app_id}")
    return {
        "app_id": app_id,
        "count": len(uuids),
        "uuids": uuids[:20],  # Return first 20 for brevity
        "total": len(uuids),
    }
