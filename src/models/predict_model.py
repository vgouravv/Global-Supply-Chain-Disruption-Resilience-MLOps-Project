import json
import os
import sys
from mlflow import mlflow
import pandas as pd
import pickle
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Ensure project root is on sys.path for script and dvc execution.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Supply Chain Disruption Mitigation Model Evaluation")


def load_test_data(file_path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        raise Exception(f"Error loading test data from {file_path}: {e}")


def load_model(model_path: str):
    try:
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        raise Exception(f"Error loading model from {model_path}: {e}")


def evaluate_model(model, X_test, y_test) -> dict:
    try:
        y_pred = model.predict(X_test)
        return {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, average='weighted', zero_division=0),
            "recall": recall_score(y_test, y_pred, average='weighted', zero_division=0),
            "f1_score": f1_score(y_test, y_pred, average='weighted', zero_division=0),
        }
    except Exception as e:
        raise RuntimeError(f"Error evaluating model: {e}")


def save_metrics(metrics: dict, output_path: str):
    try:
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=4)
    except Exception as e:
        raise Exception(f"Error saving metrics to {output_path}: {e}")


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    test_data_path = os.path.join(project_root, "data", "processed", "test_processed.csv")
    model_path = os.path.join(project_root, "models", "model.pkl")
    reports_dir = os.path.join(project_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    metrics_path = os.path.join(reports_dir, "metrics.json")

    test_data = load_test_data(test_data_path)
    if 'Mitigation_Action_Taken' not in test_data.columns:
        raise ValueError("Target column 'Mitigation_Action_Taken' not found in test data")

    X_test = test_data.drop('Mitigation_Action_Taken', axis=1)
    y_test = test_data['Mitigation_Action_Taken']

    model = load_model(model_path)
    metrics = evaluate_model(model, X_test, y_test)
    save_metrics(metrics, metrics_path)

    # Log evaluation metrics to MLflow
    with mlflow.start_run():
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, float(metric_value))
        # Optionally log the evaluation report artifact
        mlflow.log_artifact(metrics_path)

    print(f"Saved evaluation metrics to {metrics_path} and MLflow run.")


if __name__ == "__main__":
    main()