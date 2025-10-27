# 使用 Python 3.11 slim 作為基礎映像 
FROM python:3.11-slim AS base

# 設定環境變數
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# 建立工作目錄
WORKDIR $APP_HOME

# 複製 requirements.txt
COPY requirements.txt .

# --- 安裝依賴 ---
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 建立非 root 使用者 (Security)
RUN adduser --disabled-password --gecos '' appuser

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# --- 最終映像 (Final Image) ---
FROM base AS final

# 複製安裝好的 Python 函式庫
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 建立非 root 使用者 (Security)
RUN adduser --disabled-password --gecos '' appuser
# 設置模型目錄權限
RUN mkdir -p $APP_HOME/app/models && chown -R appuser:appuser $APP_HOME/app/models

# 複製應用程式程式碼
COPY app $APP_HOME/app
COPY crm_mock $APP_HOME/crm_mock
COPY mlops $APP_HOME/mlops

# 設定非 root 使用者 (Security)
USER appuser

# 暴露 FastAPI 服務端口
EXPOSE 8000

# 啟動 FastAPI 服務
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
