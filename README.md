# Global Supply Chain Mitigation Recommender

A production-grade **MLOps pipeline** that predicts supply chain disruptions and recommends real-time mitigation strategies. This project combines **prescriptive analytics** with machine learning to help businesses minimize delays and optimize resilience.

---

## 🎯 Problem Statement

Supply chain disruptions (weather events, transportation failures, order delays) cost businesses billions annually. Traditional analytics can *predict* delays, but don't recommend actions to prevent them.

**The gap:** Prediction without prescription = reactive, not proactive.

---

## 💡 Solution

This project provides:

1. **Disruption Prediction**: Random Forest classifier predicts mitigation actions needed based on supply chain context
2. **DVC Pipeline**: Reproducible, version-controlled end-to-end ML workflow
3. **Production Ready**: FastAPI service deployment, structured artifacts, full traceability
4. **Prescriptive Output**: Not just "delay predicted" — but "take action X, Y, Z"

---

## 🏗️ Project Stack

- **ML Framework**: scikit-learn (Random Forest)
- **Data Pipeline**: DVC (Data Version Control)
- **API**: FastAPI + Uvicorn
- **Requirements**: Python 3.11+
- **Data Source**: Kaggle datasets (via kagglehub)
- **Serialization**: Joblib (columns), Pickle (trained model)

---

## 📋 Setup Instructions

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd Global-Supply-Chain-Disruption-Resilience-MLOps-Project
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Add Data

Place your supply chain dataset (CSV) in `data/external/`:

```bash
cp /path/to/your/data.csv data/external/
```

**Expected columns:**
- Order_ID, Order_Date
- Route_Type, Destination_City, Origin_City
- Delivery_Status, Transportation_Mode, Product_Category
- Disruption_Event, Mitigation_Action_Taken (target)

### 3. Run Pipeline

```bash
python -m dvc repro
```

This executes all stages in sequence:
1. **data_collection**: Load raw CSV, split into train/test
2. **pre_processing**: Drop irrelevant features, one-hot encode categorical variables
3. **model_building**: Train Random Forest on training data
4. **model_eval**: Evaluate on test set, save metrics

Outputs:
- `data/raw/train.csv`, `data/raw/test.csv` (split data)
- `data/processed/train_processed.csv`, `data/processed/test_processed.csv` (engineered features)
- `models/model.pkl` (trained model artifact)
- `models/columns.pkl` (feature column order)
- `reports/metrics.json` (evaluation metrics: accuracy, precision, recall, F1)

### 4. Start MLflow Tracking Server

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Open `http://127.0.0.1:5000` to view experiments, runs, and model registry.

### 5. Deploy API

```bash
uvicorn main:app --reload
```

### 6. Deploy with Docker

For full pipeline execution, place your dataset in `data/external/` before building.

```bash
# Place data
cp /path/to/your/data.csv data/external/

# Build & orchestrate
docker-compose up --build
```

This starts:
- MLflow server on `http://localhost:5000`
- Training service: runs `dvc repro` if data exists, else skips
- FastAPI API on `http://localhost:8000` (waits for training)

Or build and run individually:

```bash
docker build -t gsc-api .
docker run -p 8000:8000 gsc-api
```

### 7. Deploy with Kubernetes

This repo includes Kubernetes manifests in `k8s/` for:
- MLflow server
- One-time training job
- FastAPI deployment
- Shared persistent volume for MLflow and model artifacts

Build the image used by training and API:

```bash
docker build -t gsc-mlops:latest .
```

Apply all Kubernetes resources:

```bash
kubectl apply -k k8s/
```

One-command rebuild + redeploy on Minikube:

```bash
./scripts/minikube-redeploy.sh
```

Alternative via Makefile:

```bash
make minikube_redeploy
```

One-command teardown (delete namespace + stop Minikube):

```bash
./scripts/minikube-cleanup.sh
```

Alternative via Makefile:

```bash
make minikube_cleanup
```

Optional flags:

```bash
# Keep namespace resources, only stop cluster
DELETE_NAMESPACE=false ./scripts/minikube-cleanup.sh

# Delete namespace but keep cluster running
STOP_CLUSTER=false ./scripts/minikube-cleanup.sh
```

Run training (creates model files in shared storage):

```bash
kubectl -n mlops delete job training --ignore-not-found
kubectl apply -k k8s/
kubectl -n mlops logs -f job/training
```

Deploy API after training data is available:

```bash
kubectl -n mlops rollout status deployment/api
kubectl -n mlops get pods,svc
```

Access services:

- API: `http://<node-ip>:30080`
- MLflow: `http://<node-ip>:30500`

For local clusters (kind/minikube/docker desktop), you can also port-forward:

```bash
kubectl -n mlops port-forward svc/api 8000:8000
kubectl -n mlops port-forward svc/mlflow 5000:5000
```

---

## 🔧 Configuration

Edit `params.yaml` to customize:

- `n_estimators`: Number of trees in Random Forest
- `model_name`: Name in MLflow Model Registry
- `model_stage`: Initial stage (Staging/Production)
- `promote_to_production`: Auto-promote to Production
- `max_test_f1_drop`: Threshold for rollback (e.g., 0.02)

---

## 📊 MLflow Model Registry

- **Automatic Registration**: Models are registered after training
- **Stage Transitions**: Configurable promotion to Staging/Production
- **Rollback Logic**: If `test_f1_score` drops > `max_test_f1_drop`, rollback to previous Production version
- **Data Versioning**: Tracks data hash and Git commit in runs

---

## 🔄 DVC Pipeline Stages

| Stage | Input | Output | Purpose |
|-------|-------|--------|---------|
| `data_collection` | `data/external/*.csv` | `data/raw/{train,test}.csv` | Load, split dataset |
| `pre_processing` | `data/raw/` | `data/processed/` | Feature engineering, encoding |
| `model_building` | `data/processed/train_processed.csv` | `models/model.pkl` | Train Random Forest |
| `model_eval` | `models/model.pkl` + test set | `reports/metrics.json` | Evaluate model performance |

---

## 📦 Project Structure

```
├── data/
│   ├── external/          ← Raw input CSVs (add your dataset here)
│   ├── raw/               ← Split train/test (auto-generated)
│   ├── interim/           ← Intermediate transformed data
│   └── processed/         ← Final engineered features
├── models/
│   ├── model.pkl          ← Trained Random Forest
│   └── columns.pkl        ← Feature column order
├── src/
│   ├── data/
│   │   └── make_dataset.py       ← Load, split data
│   ├── features/
│   │   └── build_features.py     ← Feature engineering
│   ├── models/
│   │   ├── train_model.py        ← Model training
│   │   └── predict_model.py      ← Evaluation
│   └── visualization/
│       └── visualize.py           ← (Future) reporting
├── reports/
│   └── metrics.json        ← Model evaluation metrics
├── dvc.yaml                ← Pipeline definition
├── dvc.lock                ← Reproducibility lock file
├── params.yaml             ← Hyperparameters
├── pyproject.toml          ← Python project metadata
└── requirements.txt        ← Dependencies
```

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Setup
python -m venv .venv
# Activate environment
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. Add your data
cp /path/to/supply_chain_data.csv data/external/

# 3. Run pipeline
dvc repro

# 4. Check results
cat reports/metrics.json
ls models/
```

---

## 📊 What Gets Produced

### Metrics (`reports/metrics.json`)
```json
{
  "accuracy": 0.87,
  "precision": 0.85,
  "recall": 0.88,
  "f1_score": 0.86
}
```

### Model Artifacts
- `models/model.pkl` — Ready-to-deploy classifier
- `models/columns.pkl` — Feature column order for inference

---

## 📌 Production Readiness Checklist

- ✅ Reproducible DVC pipeline (versioned with `dvc.lock`)
- ✅ Python 3.11+ required (specified in `pyproject.toml`)
- ✅ All artifacts in structured directories (`models/`, `data/processed/`)
- ✅ Explicit error handling (missing data fails gracefully)
- ✅ Git-ready (committed `requirements.txt`, `dvc.yaml`, locked versions)
- ✅ Idempotent pipeline (safe to re-run, won't fail on existing dirs)

---

## 🔐 Data Privacy

- Raw data stored in `data/external/` (not committed to Git)
- Add `data/external/` to `.gitignore` if sensitive
- Use `dvc remote` to push data to secure cloud storage (S3, Azure, GCS)

---

## 📚 Next Steps

1. **Integration Testing**: Add unit tests in `tests/`
2. **CI/CD**: GitHub Actions workflow for `dvc repro` on push
3. **Model Serving**: Deploy FastAPI endpoint for real-time inference
4. **Monitoring**: Add MLflow or similar for metric tracking
5. **Explainability**: SHAP values for feature importance

---

## 🤝 Contributing

1. Create feature branch
2. Make changes + test locally
3. Run `dvc repro` to validate pipeline
4. Commit `dvc.lock` (never modify manually)
5. Push & open PR

---

> Citation: Gourav Sahu (2026). *Global Supply Chain Mitigation Recommender*.

---

## 📄 License

See LICENSE file

---
