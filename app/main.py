from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import joblib
import os
import logging
import httpx 
import random 
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List

# --- 1. Prometheus Metrics Definitions (M5 修正: MODEL_HEALTH 改為 Gauge) ---
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP request latency (seconds)', ['method', 'endpoint']
)
PREDICTION_COUNT = Counter(
    'ai_prediction_requests_total', 'Total prediction requests to the model'
)
PREDICTION_ERROR_COUNT = Counter(
    'ai_prediction_errors_total', 'Total prediction errors'
)
# 使用 Gauge 追蹤模型健康狀態 (1=Loaded, 0=Failed/Not Loaded)
MODEL_HEALTH_GAUGE = Gauge(
    'ai_model_loaded', 'Model loading status (1=Loaded, 0=Failed)', ['model_version']
)
# -------------------------------------------------------------------------

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AI Service] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CRM Mock 服務的 URL，透過 Docker Compose 的服務名稱解析
CRM_HOST = os.getenv("CRM_HOST", "http://crm_mock:8001") 

app = FastAPI(title="AI Model Integration Service",
              description="Demonstrates integrating a machine learning model via FastAPI and exposing Prometheus metrics.")

# Define request body schema
class PredictionRequest(BaseModel):
    # Features must match the 10 features expected by train_model.py
    features: List[float]

# Define response body schema
class PredictionResponse(BaseModel):
    prediction: int
    model_version: str

MODEL = None
MODEL_VERSION = os.getenv("MODEL_VERSION", "v0.0.0-unloaded")
MODEL_PATH = "app/models/sample_model.joblib" # Path within the container
FEATURE_COUNT = 10

@app.on_event("startup")
async def load_model():
    """Load the ML model when the FastAPI application starts."""
    global MODEL, MODEL_VERSION
    if os.path.exists(MODEL_PATH):
        try:
            MODEL = joblib.load(MODEL_PATH)
            logger.info(f"模型 {MODEL_PATH} (版本: {MODEL_VERSION}) 載入成功.")
            # 設定 Gauge 指標
            MODEL_HEALTH_GAUGE.labels(model_version=MODEL_VERSION).set(1) 
        except Exception as e:
            logger.error(f"從 {MODEL_PATH} 載入模型失敗: {e}")
            MODEL = None
            MODEL_HEALTH_GAUGE.labels(model_version=MODEL_VERSION).set(0)
    else:
        logger.warning(f"模型檔案未找到於 {MODEL_PATH}. 預測端點將無法運作.")
        MODEL_HEALTH_GAUGE.labels(model_version=MODEL_VERSION).set(0)


# --- Prometheus Middleware for general HTTP monitoring ---
class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        
        with REQUEST_LATENCY.labels(method, endpoint).time():
            response = await call_next(request)
        
        # Increment request counter
        status_code = response.status_code
        REQUEST_COUNT.labels(method, endpoint, status_code).inc()
        
        return response

app.add_middleware(PrometheusMiddleware)
# --------------------------------------------------------


# --- API Endpoints ---
@app.get("/")
async def health_check():
    """健康檢查端點."""
    return {"status": "ok", "service": "AI 模型整合服務", "model_loaded": MODEL is not None, "model_version": MODEL_VERSION}

@app.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(request: PredictionRequest):
    """
    預測端點：對輸入特徵進行分類預測.
    """
    PREDICTION_COUNT.inc()
    
    if len(request.features) != FEATURE_COUNT:
        raise HTTPException(status_code=422, detail=f"特徵數量錯誤。預期 {FEATURE_COUNT} 個特徵，收到 {len(request.features)} 個。")

    if MODEL is None:
        PREDICTION_ERROR_COUNT.inc()
        raise HTTPException(status_code=503, detail="模型未載入。請確認模型檔案是否存在。")

    try:
        prediction = MODEL.predict([request.features])[0]
        return PredictionResponse(prediction=int(prediction), model_version=MODEL_VERSION)
    except Exception as e:
        PREDICTION_ERROR_COUNT.inc()
        logger.error(f"預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預測錯誤: {e}")

@app.post("/crm_segment_update")
async def crm_segment_update(customer_id: str):
    """
    M4C1/M4C2 實作：從 CRM 查詢特徵 -> 預測 -> 更新 CRM 分群。
    此邏輯更貼近生產環境的實務流程。
    """
    logger.info(f"收到客戶分群更新請求 ID: {customer_id}")
    
    if MODEL is None:
        raise HTTPException(status_code=503, detail="模型未載入，無法執行分群邏輯。")

    try:
        # --- 步驟 1: 從 CRM Mock 服務獲取客戶特徵 (更貼近實務) ---
        async with httpx.AsyncClient(base_url=CRM_HOST, timeout=5.0) as client:
            # 呼叫 CRM 的特徵獲取端點
            feature_response = await client.get(f"/customer/{customer_id}/features")
            feature_response.raise_for_status()
            customer_features = feature_response.json().get("features")
            
            if not customer_features or len(customer_features) != FEATURE_COUNT:
                 logger.error(f"從 CRM 獲取特徵失敗或特徵數不匹配。")
                 raise HTTPException(status_code=400, detail="無法獲取有效客戶特徵或特徵數量不正確。")

        logger.info(f"  [1] 從 CRM 獲取特徵成功: {customer_features[:3]}...")
        
        # --- 步驟 2: 呼叫模型進行預測 ---
        prediction_request = PredictionRequest(features=customer_features)
        prediction_response = await predict_endpoint(prediction_request)
        model_output = prediction_response.prediction
        logger.info(f"  [2] 模型預測輸出 (0/1): {model_output}")
        
        # --- 步驟 3: 執行業務邏輯 (M4C2) ---
        if model_output == 1:
            new_segment = "Churn_Risk_AI"
        else:
            new_segment = "Normal_Segment_AI"
            
        logger.warning(f"  [3] 業務決策: 客戶 {customer_id} -> 新分群: {new_segment}")
        
        # --- 步驟 4: 呼叫 Mock CRM 服務更新 (M4C1) ---
        async with httpx.AsyncClient(base_url=CRM_HOST, timeout=5.0) as client:
            crm_update_data = {"user_id": customer_id, "ai_segment": new_segment}
            crm_response = await client.post(
                "/crm_segment_update", 
                json=crm_update_data
            )

        crm_response.raise_for_status()
        crm_result = crm_response.json()
        
        logger.info(f"  [4] CRM 更新成功! 結果: {crm_result}")
        
        return {
            "customer_id": customer_id, 
            "status": "Success", 
            "segment_ai_decision": new_segment,
            "crm_mock_response": crm_result
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"呼叫 CRM 失敗 (HTTP 錯誤): {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=502, detail=f"CRM Mock 服務返回錯誤: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"呼叫 CRM 失敗 (連線錯誤): {e}")
        raise HTTPException(status_code=503, detail=f"無法連線到 CRM Mock 服務: {CRM_HOST}")
    except Exception as e:
        logger.error(f"分群處理發生未預期錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"分群邏輯執行錯誤: {e}")


@app.get("/metrics")
async def metrics():
    """Prometheus 指標端點."""
    return Response(content=generate_latest(), media_type="text/plain; charset=utf-8")
