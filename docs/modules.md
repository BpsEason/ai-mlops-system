# AI 模型整合與部署教學模組指南 (M1 - M6)

## M1: 專案初始化與結構定義
- **目標:** 建立標準的 MLOps 專案骨架，熟悉工具鏈。
- **產出:** 完整的專案目錄結構、`requirements.txt`、`.env` 環境變數。

## M2: 模型服務化與部署
- **目標:** 將訓練好的模型部署為可供業務系統呼叫的 API 服務。
- **產出:** - `app/main.py`: 實現模型載入、`/predict` 端點。
  - `Dockerfile`: 服務容器化，使用非 root 用戶。

## M3: MLOps 實驗與版本管理 (MLflow)
- **目標:** 使用 MLflow 追蹤模型實驗、管理模型版本並註冊到 Registry。
- **產出:** - `mlops/train_model.py`: 記錄參數、指標、註冊模型。
  - MLflow UI 記錄可供查閱。

## M4: 跨系統整合與業務邏輯
- **目標:** 實現 AI 服務與外部業務系統（CRM）的互動。
- **產出:** - AI 服務中實現從 CRM **查詢特徵**，進行預測，並將結果回寫到 CRM 的邏輯。
  - `crm_mock/main.py`: 模擬外部系統 API。

## M5: 監控與可觀測性 (M&O)
- **目標:** 導入 Prometheus 和 Grafana，對 AI 服務的健康和性能進行實時監控。
- **產出:** - `app/main.py`: 暴露 Prometheus 指標（請求數、延遲、模型健康 Gauge）。
  - Prometheus/Grafana 啟動，儀表板自動載入並顯示關鍵指標。

## M6: 自動化測試與驗收
- **目標:** 建立單元測試和集成測試，確保服務的穩定性，並納入 CI/CD 流程。
- **產出:** - `tests/test_api.py`: 包含單元測試和**跨服務集成測試**（驗證 CRM 更新）。
  - `.github/workflows/ci.yml`: CI/CD 流程成功執行。
