import pytest
from fastapi.testclient import TestClient
from app.main import app as fastapi_app  # 假設 app.main 已經存在
import requests
import time

# 使用 TestClient 進行測試
client = TestClient(fastapi_app)

# --- 測試數據 ---
VALID_FEATURES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
INVALID_FEATURES = [1.0, 2.0] # 錯誤的特徵數量
TEST_CUSTOMER_ID = "CUST_TEST_007"
CRM_MOCK_URL = "http://crm_mock:8001" 

# --- 1. 基本服務測試 ---

def test_health_check():
    """測試服務健康檢查端點 (M2C4 驗收)。"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_prometheus_metrics_endpoint():
    """測試 Prometheus 指標端點是否可存取 (M5C1 驗收)。"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    # 檢查 Gauge 是否存在
    assert "ai_model_loaded" in response.text 
    assert "ai_prediction_requests_total" in response.text

# --- 2. 預測服務測試 (M2C1 驗收) ---

def test_prediction_with_valid_data():
    """測試模型載入後，使用有效數據進行預測。"""
    response_health = client.get("/")
    # 允許在模型未載入時返回 503
    if not response_health.json().get("model_loaded"):
        response = client.post("/predict", json={"features": VALID_FEATURES})
        assert response.status_code == 503
        return 

    response = client.post("/predict", json={"features": VALID_FEATURES})
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert isinstance(data["prediction"], int)

def test_prediction_with_invalid_feature_count():
    """測試特徵數量不匹配的數據 (Pydantic 驗證失敗)。"""
    response = client.post("/predict", json={"features": INVALID_FEATURES})
    assert response.status_code == 422

# --- 3. 跨系統整合測試 (M4C1/M4C2, M6 驗收增強) ---

@pytest.mark.external
def test_crm_integration_flow():
    """
    測試 AI 服務中的 /crm_segment_update 端點是否能正確呼叫 CRM Mock 
    並驗證 CRM 數據是否確實更新。
    """
    try:
        # 1. 檢查 CRM Mock 服務是否可訪問
        requests.get(f"{CRM_MOCK_URL}/health").raise_for_status()
    except requests.exceptions.ConnectionError:
        pytest.skip(f"無法連線到 CRM Mock 服務於 {CRM_MOCK_URL}。請確認 docker-compose 是否啟動。")
    except requests.exceptions.HTTPError:
        pytest.skip(f"CRM Mock 服務運行異常於 {CRM_MOCK_URL}。")
        
    # 2. 執行 AI 服務的整合端點 (觸發特徵查詢、預測和 CRM 呼叫)
    response = client.post(f"/crm_segment_update?customer_id={TEST_CUSTOMER_ID}")
    
    # 預期：200 OK，表示 AI 服務成功執行了邏輯並與 CRM 成功互動
    assert response.status_code == 200
    data = response.json()
    new_segment = data["segment_ai_decision"]
    
    # 3. 驗證 CRM Mock 數據是否更新 (M6 增強點: 驗證 CRM 實際狀態)
    # 直接呼叫 CRM Mock 的 GET 端點進行驗證
    crm_data_response = requests.get(f"{CRM_MOCK_URL}/customer/{TEST_CUSTOMER_ID}")
    crm_data_response.raise_for_status()
    crm_data = crm_data_response.json()

    assert crm_data["user_id"] == TEST_CUSTOMER_ID
    assert crm_data["segment"] == new_segment # 驗證分群標籤已更新
