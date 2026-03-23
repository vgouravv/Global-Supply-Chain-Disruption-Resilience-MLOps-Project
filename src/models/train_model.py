import os
import sys
import hashlib
import pickle
import mlflow
import pandas as pd
from ruamel.yaml import YAML
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from mlflow.tracking import MlflowClient
import mlflow.sklearn

# Ensure project root is on sys.path for script and dvc execution.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.predict_model import evaluate_model

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Supply Chain Disruption Mitigation Model Evaluation")

def load_data(file_path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        raise Exception(f"Error loading data from {file_path}: {e}")


def load_params(filepath: str) -> dict:
    try:
        yaml = YAML(typ='safe')
        with open(filepath) as f:
            params = yaml.load(f)
        return params.get("model_building", {})
    except Exception as e:
        raise Exception(f"Error loading parameters from {filepath}: {e}")


def train_model(X: pd.DataFrame, y: pd.Series, n_estimators: int) -> RandomForestClassifier:
    try:
        model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
        model.fit(X, y)
        return model
    except Exception as e:
        raise RuntimeError(f"Error training model: {e}")


def compute_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def save_model(model, output_path: str):
    try:
        with open(output_path, "wb") as f:
            pickle.dump(model, f)
    except Exception as e:
        raise Exception(f"Error saving model to {output_path}: {e}")


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    processed_data_path = os.path.join(project_root, "data", "processed", "train_processed.csv")
    param_file_path = os.path.join(project_root, "params.yaml")
    models_dir = os.path.join(project_root, "models")
    os.makedirs(models_dir, exist_ok=True)
    model_output_path = os.path.join(models_dir, "model.pkl")

    data = load_data(processed_data_path)
    if "Mitigation_Action_Taken" not in data.columns:
        raise ValueError("Target column 'Mitigation_Action_Taken' not found in training data")
 
    X_train = data.drop("Mitigation_Action_Taken", axis=1)
    y_train = data["Mitigation_Action_Taken"]

    params = load_params(param_file_path)
    n_estimators = params.get("n_estimators")
    if n_estimators is None:
        raise ValueError(f"n_estimators is missing in params.yaml under model_building; got: {params}")
    n_estimators = int(n_estimators)
    print(f"Using n_estimators from params.yaml: {n_estimators}")

    # Data versioning: add hash and (optional) git commit
    data_hash = compute_file_hash(processed_data_path)
    git_commit = None
    try:
        import subprocess
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root).strip().decode()
    except Exception:
        git_commit = None

    with mlflow.start_run():
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("train_data_hash", data_hash)
        if git_commit:
            mlflow.log_param("git_commit", git_commit)

        model = train_model(X_train, y_train, n_estimators)

        # training set score (if no validation set in this script)
        y_pred_train = model.predict(X_train)
        train_accuracy = accuracy_score(y_train, y_pred_train)
        mlflow.log_metric("train_accuracy", float(train_accuracy))

        # optionally evaluate on test set (external) and log metrics
        test_data_path = os.path.join(project_root, "data", "processed", "test_processed.csv")
        if os.path.exists(test_data_path):
            test_data = pd.read_csv(test_data_path)
            if "Mitigation_Action_Taken" in test_data.columns:
                X_test = test_data.drop("Mitigation_Action_Taken", axis=1)
                y_test = test_data["Mitigation_Action_Taken"]
                test_metrics = evaluate_model(model, X_test, y_test)
                for k, v in test_metrics.items():
                    mlflow.log_metric(f"test_{k}", float(v))

        # save model artifact
        mlflow.sklearn.log_model(model, "random_forest_model")

        # register model in MLflow Model Registry
        run_id = mlflow.active_run().info.run_id
        model_uri = f"runs:/{run_id}/random_forest_model"
        model_name = params.get("model_name", "SupplyChainRandomForest")

        try:
            registration = mlflow.register_model(model_uri, model_name)
            print(f"Model registered as {model_name} from {model_uri}")

            # transition model version stage
            target_stage = params.get("model_stage", "Staging")
            client = MlflowClient()
            model_version = registration.version
            client.transition_model_version_stage(
                name=model_name,
                version=model_version,
                stage=target_stage,
                archive_existing_versions=True,
            )
            print(f"Model version {model_version} transitioned to stage {target_stage}")

            # optional automated promotion to Production (after Staging is set)
            if params.get("promote_to_production", False):
                client.transition_model_version_stage(
                    name=model_name,
                    version=model_version,
                    stage="Production",
                    archive_existing_versions=True,
                )
                print(f"Model version {model_version} transitioned to Production")

            # check test f1 drop vs existing production version
            test_f1 = None
            if "test_metrics" in locals() and "f1_score" in test_metrics:
                test_f1 = float(test_metrics["f1_score"])

            max_drop = float(params.get("max_test_f1_drop", 0.02))
            if test_f1 is not None:
                prod_versions = client.get_latest_versions(model_name, stages=["Production"])
                if prod_versions:
                    prod_run = client.get_run(prod_versions[0].run_id)
                    prod_test_f1 = prod_run.data.metrics.get("test_f1_score")
                    if prod_test_f1 is not None:
                        prod_test_f1 = float(prod_test_f1)
                        print(f"Production test_f1={prod_test_f1} vs current test_f1={test_f1}")
                        if test_f1 < prod_test_f1 - max_drop:
                            # rollback: keep production version, archive candidate
                            client.transition_model_version_stage(
                                name=model_name,
                                version=model_version,
                                stage="Archived",
                                archive_existing_versions=False,
                            )
                            client.transition_model_version_stage(
                                name=model_name,
                                version=prod_versions[0].version,
                                stage="Production",
                                archive_existing_versions=True,
                            )
                            print(f"Rollback triggered: model {model_version} archived due to f1 drop")
                        else:
                            print(f"Model {model_version} meets f1 threshold; no rollback needed")
                else:
                    print("No existing Production version; no rollback check needed")
        except Exception as e:
            print(f"Model registry registration failed: {e}")

        save_model(model, model_output_path)

    print(f"MLflow run completed with train_accuracy={train_accuracy:.4f}")
    if os.path.exists(test_data_path) and "test_metrics" in locals():
        print(f"MLflow run completed with test metrics: {test_metrics}")


if __name__ == "__main__":
    main()