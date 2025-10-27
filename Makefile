.PHONY: up down train test clean

# 服務名稱
COMPOSE_FILE = docker-compose.yml

# 預設訓練參數
SAMPLES ?= 1000
VERSION ?= v1.0.0-auto

# 啟動所有服務 (Build + Run)
up:
	docker-compose -f ${COMPOSE_FILE} up --build -d

# 停止所有服務
down:
	docker-compose -f ${COMPOSE_FILE} down

# 訓練模型 (M3)
# 使用 run --rm 確保每次都是乾淨的運行環境
train:
	@echo "--- 1. 確保 MLflow Server 運行 ---"
	docker-compose -f ${COMPOSE_FILE} up -d mlflow_server
	@echo "--- 2. 執行模型訓練腳本 --- (版本: ${VERSION}, 樣本: ${SAMPLES})"
	docker-compose -f ${COMPOSE_FILE} run --rm mlflow_server python mlops/train_model.py --n_samples ${SAMPLES} --model_version ${VERSION}

# 執行單元測試 (M6)
# -m "not external" 排除需要外部服務的測試
test:
	@echo "--- 執行單元測試 (排除外部服務) ---"
	docker-compose -f ${COMPOSE_FILE} run --rm fastapi_app pytest tests/test_api.py -m "not external"

# 執行集成測試 (M6)
# -m "external" 執行需要 CRM/FastAPI 互聯的測試
integration_test:
	@echo "--- 執行集成測試 (需要所有服務運行) ---"
	docker-compose -f ${COMPOSE_FILE} run --rm fastapi_app pytest tests/test_api.py -m "external"

# 清理所有資源 (容器、網路、掛載的資料)
clean:
	@echo "--- 清理所有容器、網路與資料 (mlflow_data/app/models) ---"
	docker-compose -f ${COMPOSE_FILE} down -v
	rm -rf mlflow_data
	rm -rf app/models/*
	@echo "清理完成。"
