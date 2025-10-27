# 🚀 AI 模型整合與部署教學系統（MLOps Teaching System）

本專案是一套針對 AI 模型整合、MLOps 流程、跨系統串接與監控驗收的教學系統，提供完整的實務環境與模組化架構，協助學員從零開始掌握 AI 工程落地的核心技能。

---

## 🎯 教學目標與模組對應

| 模組 | 主題 | 核心能力 | 對應實作 |
|------|------|-----------|-----------|
| M1 | 專案初始化與環境建構 | 專案結構、依賴管理、Makefile 操作 | `requirements.txt`, `.env`, `Makefile` |
| M2 | 模型服務化與容器部署 | FastAPI 架構、Dockerfile、API 設計 | `app/main.py`, `Dockerfile`, `docker-compose.yml` |
| M3 | 模型訓練與版本控管 | MLflow 實驗追蹤、模型註冊、CLI 參數化 | `mlops/train_model.py`, `mlflow_server` |
| M4 | 跨系統整合與業務邏輯 | CRM 特徵查詢、預測決策、資料更新 | `app/main.py`, `crm_mock/main.py` |
| M5 | 監控與可觀測性 | Prometheus 指標、Grafana 儀表板 | `prometheus.yml`, `grafana_config/` |
| M6 | 自動化測試與驗收 | pytest 測試、CI/CD 工作流、資料驗證 | `tests/test_api.py`, `.github/workflows/ci.yml` |

---

## 🧱 系統架構總覽

本系統採用容器化部署，整合以下元件：

| 服務 | 端口 | 功能說明 |
|------|------|----------|
| `fastapi_app` | 8000 | AI 預測服務，支援 CRM 整合與 Prometheus 指標 |
| `mlflow_server` | 5000 | 模型訓練追蹤與版本註冊中心 |
| `crm_mock` | 8001 | 模擬 CRM 系統，支援特徵查詢與分群更新 |
| `prometheus` | 9090 | 指標收集與監控 |
| `grafana` | 3000 | 視覺化儀表板，展示 AI 系統健康狀態與效能 |

---

## ⚙️ 快速啟動流程

### 1️⃣ 初始化環境（M1）

```bash
git clone <your-repo>
cd ai-mlops-system
cp .env.example .env  # 設定 MODEL_VERSION
```

### 2️⃣ 訓練模型並註冊（M3）

```bash
make train  # 預設訓練 1000 筆樣本，版本 v1.0.0
make train VERSION=v2.0.0-large SAMPLES=5000  # 自訂版本與樣本數
```

### 3️⃣ 啟動所有服務（M2/M4/M5）

```bash
docker-compose up --build -d
```

### 4️⃣ 驗證系統狀態（M6）

```bash
make test  # 執行 pytest 測試，驗證預測與 CRM 整合邏輯
```

---

## 📊 Grafana 儀表板預覽（M5）

- 模型健康狀態（Gauge）
- 預測請求數與錯誤率（Counter）
- API 延遲分佈（Histogram）
- CRM 整合成功率（自訂指標）

---

## 🧪 驗收與擴充建議

- ✅ 完成 M1–M6 模組後，可進行 Rubric 驗收與 Badge 評量
- 🔄 可擴充模組：推薦系統、分群行銷、K8s 部署、CI/CD 測試覆蓋率
- 📦 建議補充：`docs/modules.md`, `docs/rubric.yml`, `docs/badges.yml`

---

## 🧠 技術亮點

- FastAPI + MLflow + Prometheus + Grafana 全堆疊整合
- 支援 CLI 參數化訓練與模型版本控管
- 非同步 CRM 整合邏輯（httpx）
- Prometheus 指標設計符合 MLOps 可觀測性原則
- Dockerfile 使用非 root 使用者，強化容器安全性
- CI/CD 工作流支援 pytest 驗收與 Docker 建構
