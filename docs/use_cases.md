# 可擴充的應用場景建議 (M5/M6 擴充方向)

## 1. 服務擴展性
- **灰度發布 (Canary Deployment):**
  - 在 K8s 中部署兩個不同版本 (如 v1.0.0 和 v1.1.0) 的 \`fastapi_app\`，使用 Istio 或 Nginx 實現 90%/10% 的流量分配。
  - 觀察 Grafana 儀表板，比較兩個版本的延遲 (Latency) 和錯誤率 (Error Rate)。

## 2. 數據漂移監控 (Data Drift)
- **M5 擴充:**
  - 修改 \`app/main.py\`，加入模型預測的輸入特徵統計收集邏輯。
  - 增加一個 Prometheus 指標，如 \`ai_feature_mean\`，追蹤某個關鍵特徵（例如 feature_1）的平均值。
  - 在 Grafana 中，將此實時指標與訓練時的靜態平均值進行比較，一旦超出閾值則發出警報。

## 3. 自動化回滾 (M3 + M6 聯動)
- **M3 擴充:** 在 \`mlops/train_model.py\` 中，只有當準確率高於某個閾值 (例如 0.85) 時才註冊模型。
- **M6 擴充:** - 設置集成測試的性能門檻 (Performance Gate)。
  - 若新版本模型部署後，集成測試的 P95 延遲超過 200ms，CI/CD 流程應自動觸發回滾到上一個穩定的模型版本。
