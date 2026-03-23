#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-minikube}"
NAMESPACE="${K8S_NAMESPACE:-mlops}"
DELETE_NAMESPACE="${DELETE_NAMESPACE:-true}"
STOP_CLUSTER="${STOP_CLUSTER:-true}"

if ! command -v minikube >/dev/null 2>&1; then
  echo "Error: minikube is not installed or not on PATH."
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "Error: kubectl is not installed or not on PATH."
  exit 1
fi

echo "[1/2] Cleaning Kubernetes resources..."
if [ "${DELETE_NAMESPACE}" = "true" ]; then
  kubectl delete namespace "${NAMESPACE}" --ignore-not-found
  echo "Namespace '${NAMESPACE}' removed (or did not exist)."
else
  echo "Skipping namespace deletion (DELETE_NAMESPACE=${DELETE_NAMESPACE})."
fi

echo "[2/2] Stopping Minikube profile '${PROFILE}'..."
if [ "${STOP_CLUSTER}" = "true" ]; then
  if minikube status -p "${PROFILE}" >/dev/null 2>&1; then
    minikube stop -p "${PROFILE}"
  else
    echo "Profile '${PROFILE}' is not running."
  fi
else
  echo "Skipping Minikube stop (STOP_CLUSTER=${STOP_CLUSTER})."
fi

echo
echo "Cleanup complete."
echo "To start again: ./scripts/minikube-redeploy.sh"
