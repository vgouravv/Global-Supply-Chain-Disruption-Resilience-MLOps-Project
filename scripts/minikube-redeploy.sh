#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-minikube}"
NAMESPACE="${K8S_NAMESPACE:-mlops}"
IMAGE_TAG="${IMAGE_TAG:-gsc-mlops:latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
K8S_DIR="${REPO_ROOT}/k8s"

if ! command -v minikube >/dev/null 2>&1; then
  echo "Error: minikube is not installed or not on PATH."
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "Error: kubectl is not installed or not on PATH."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not on PATH."
  exit 1
fi

if [ ! -d "${K8S_DIR}" ]; then
  echo "Error: Kubernetes directory not found at ${K8S_DIR}."
  exit 1
fi

echo "[1/6] Ensuring Minikube profile '${PROFILE}' is running..."
if ! minikube status -p "${PROFILE}" >/dev/null 2>&1; then
  minikube start -p "${PROFILE}" --driver=docker --cpus=2 --memory=4096
fi

echo "[2/6] Building image '${IMAGE_TAG}' inside Minikube Docker daemon..."
eval "$(minikube -p "${PROFILE}" docker-env)"
docker build -q -t "${IMAGE_TAG}" "${REPO_ROOT}"

echo "[3/6] Applying Kubernetes manifests from ${K8S_DIR}..."
kubectl apply -k "${K8S_DIR}"

echo "[4/6] Recreating training job to force a fresh run..."
kubectl -n "${NAMESPACE}" delete job training --ignore-not-found
kubectl apply -k "${K8S_DIR}"

echo "[5/6] Waiting for training to complete..."
if ! kubectl -n "${NAMESPACE}" wait --for=condition=complete job/training --timeout=30m; then
  echo "Training job failed or timed out. Recent logs:"
  kubectl -n "${NAMESPACE}" logs job/training --tail=200 || true
  exit 1
fi

echo "[6/6] Restarting API deployment and waiting for rollout..."
kubectl -n "${NAMESPACE}" rollout restart deployment/api
kubectl -n "${NAMESPACE}" rollout status deployment/api --timeout=10m

echo
echo "Redeploy complete."
echo "Training job: training"
echo "API URL: $(minikube -p "${PROFILE}" service -n "${NAMESPACE}" api --url | head -n 1)"
echo "MLflow URL: $(minikube -p "${PROFILE}" service -n "${NAMESPACE}" mlflow --url | head -n 1)"
echo "Check pods: kubectl -n ${NAMESPACE} get pods"
