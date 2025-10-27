from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from typing import Dict, Any, List
import random # 用於模擬特徵生成

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CRM Mock] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="CRM Mock Service",
              description="A mock service simulating a Customer Relationship Management system.")

# 模擬資料庫：存放客戶資料 (用於 M4/M6 測試)
MOCK_DATABASE: Dict[str, Dict[str, Any]] = {
    "CUST001": {"name": "Alice", "segment": "High-Value", "risk_score": 0.15},
    "CUST002": {"name": "Bob", "segment": "Standard", "risk_score": 0.50},
    "CUST003": {"name": "Charlie", "segment": "Churn-Risk", "risk_score": 0.92},
    "CUST_TEST_007": {"name": "TestUser", "segment": "Pre-Test", "risk_score": 0.3} # 測試專用
}

# --- Pydantic Schemas ---
class CrmUpdateRequest(BaseModel):
    user_id: str
    ai_segment: str # 來自 AI 服務的新分群標籤

class FeatureResponse(BaseModel):
    user_id: str
    feature_count: int
    features: List[float]
    
# --- API Endpoints ---
@app.get("/health", tags=["System"])
def health_check():
    """健康檢查端點."""
    return {"service": "CRM Mock", "status": "Ready"}

@app.get("/customer/{user_id}/features", response_model=FeatureResponse, tags=["CRM"])
def get_customer_features(user_id: str):
    """
    M4C1: 模擬從 CRM 獲取 AI 模型所需的原始特徵數據 (10 features)。
    使用 user_id 的 hash 值作為種子，確保每次獲取相同的特徵，模擬數據一致性。
    """
    
    # 使用 user_id 的 hash 值作為種子
    try:
        seed = sum(ord(c) for c in user_id)
    except:
        seed = 42 # Fallback
        
    random.seed(seed)
    # 產生 10 個與 train_model.py 模擬數據範圍一致的特徵 (0.1 ~ 10.0)
    customer_features = [random.uniform(0.1, 10.0) for _ in range(10)]
    
    logger.info(f"📊 為客戶 {user_id} 模擬生成特徵 (Seed: {seed})")
    
    return FeatureResponse(
        user_id=user_id,
        feature_count=10,
        features=customer_features
    )

@app.get("/customer/{user_id}", tags=["CRM"])
def get_customer_by_id(user_id: str):
    """
    M6: 獲取客戶的當前資料，用於測試驗證分群更新結果。
    """
    if user_id not in MOCK_DATABASE:
        raise HTTPException(status_code=404, detail=f"客戶 ID {user_id} 未找到。")
    return {"user_id": user_id, **MOCK_DATABASE[user_id]}


@app.post("/crm_segment_update", tags=["CRM"])
def crm_segment_update_endpoint(request: CrmUpdateRequest):
    """
    M4C1: 接收 AI 服務推斷出的用戶分群，並更新 CRM 系統中的用戶資料。
    """
    customer_id = request.user_id
    new_segment = request.ai_segment
    
    if customer_id not in MOCK_DATABASE:
        MOCK_DATABASE[customer_id] = {"name": f"UnknownUser_{customer_id}", "segment": new_segment, "risk_score": 0.0}
        logger.info(f"🆕 客戶 {customer_id} 不存在，模擬創建並設置分群為: {new_segment}")
        return {"status": "created_and_updated", "user_id": customer_id, "new_segment": new_segment}
    
    old_segment = MOCK_DATABASE[customer_id]["segment"]
    MOCK_DATABASE[customer_id]["segment"] = new_segment
    
    logger.warning(f"🔄 客戶 {customer_id} 的分群已更新: {old_segment} -> {new_segment}")
    
    return {
        "status": "success", 
        "user_id": customer_id,
        "old_segment": old_segment,
        "new_segment": new_segment
    }

if __name__ == "__main__":
    uvicorn.run("crm_mock.main:app", host="0.0.0.0", port=8001)
