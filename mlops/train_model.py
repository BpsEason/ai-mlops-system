import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
import os
import mlflow
import mlflow.sklearn
import numpy as np
import argparse # 引入 argparse 處理 CLI 參數

# --- 1. 配置 MLflow ---
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("ai_deployment_tutorial_churn_prediction")

print(f"MLflow Tracking URI: {MLFLOW_TRACKING_URI}")

# --- 2. 模擬數據生成 (10 Features) ---
def generate_data(n_samples, n_features=10):
    np.random.seed(42)
    # 模擬客戶特徵
    X = np.random.rand(n_samples, n_features) * 10
    
    # 模擬目標變數 (Y)：流失 (1) 或未流失 (0)
    weights = np.array([0.5, -0.3, 0.8, -0.1, 0.2, 0.1, -0.4, 0.6, -0.2, 0.3])
    bias = -2.0
    linear_combination = np.dot(X, weights) + bias
    probabilities = 1 / (1 + np.exp(-linear_combination))
    y = (probabilities > 0.5).astype(int)
    
    feature_names = [f'feature_{i+1}' for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df['target'] = y
    
    return df, feature_names

if __name__ == "__main__":
    # --- CLI 參數處理 (可執行性優化) ---
    parser = argparse.ArgumentParser(description="訓練並註冊流失預測模型 (Logistic Regression).")
    parser.add_argument('--n_samples', type=int, default=1000, help='用於訓練的樣本數量.')
    parser.add_argument('--c_param', type=float, default=0.1, help='Logistic Regression 的懲罰係數 C.')
    parser.add_argument('--model_version', type=str, default='v1.0.0-auto', help='模型的版本標籤.')
    
    args = parser.parse_args()
    
    df, feature_names = generate_data(n_samples=args.n_samples)
    X = df[feature_names]
    y = df['target']
    
    # 參數定義 (M3C1 追蹤重點)
    random_state = 42
    C_param = args.c_param 
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=random_state)
    
    with mlflow.start_run() as run:
        print(f"💡 開始訓練 Logistic Regression 模型 (樣本數: {args.n_samples}, 版本: {args.model_version})...")
        
        # --- 3. 模型訓練 ---
        model = LogisticRegression(C=C_param, random_state=random_state)
        model.fit(X_train, y_train)
        
        # --- 4. 評估 ---
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"✅ 模型準確率 (Accuracy): {accuracy:.4f}")
        
        # --- 5. MLflow 記錄 (M3C1) ---
        mlflow.log_param("n_samples", args.n_samples) # 記錄樣本數
        mlflow.log_param("C", C_param)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("model_version_tag", args.model_version) # 記錄版本標籤
        mlflow.log_metric("accuracy", accuracy)
        
        # --- 6. 模型保存與註冊 (M3C1, M2C3 載入) ---
        model_save_path = os.path.join(os.getcwd(), 'app', 'models', 'sample_model.joblib')
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
        joblib.dump(model, model_save_path)
        print(f"💾 模型已保存至: {model_save_path}")
        
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="sklearn_model",
            registered_model_name="ChurnPredictionModel",
            signature=mlflow.models.infer_signature(X_train, y_train)
        )
        print("📝 模型已註冊到 MLflow Model Registry.")

    print(f"⭐ 訓練完成! MLflow Run ID: {run.info.run_id}")
