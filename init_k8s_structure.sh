#!/bin/bash

echo "📦 Creating Kubernetes manifest structure..."

# Create Kubernetes base directory
mkdir -p k8s/base

# Create manifest files
touch k8s/base/namespace.yaml
touch k8s/base/postgres.yaml
touch k8s/base/redis.yaml
touch k8s/base/grafana.yaml
touch k8s/base/go-logger.yaml
touch k8s/base/python-logger.yaml
touch k8s/base/elixir-logger.yaml
touch k8s/base/README.md

echo "✅ Kubernetes structure ready."

# Optional: Add helpful comments to README
cat <<EOF > k8s/base/README.md
# Kubernetes Base Manifests

This folder contains the Kubernetes YAML manifests for:

- `namespace.yaml` – Defines the \`search-logger\` namespace
- `postgres.yaml` – PostgreSQL deployment and service
- `redis.yaml` – Redis deployment and service
- `grafana.yaml` – Grafana deployment and service
- `go-logger.yaml` – Go backend
- `python-logger.yaml` – Python backend
- `elixir-logger.yaml` – Elixir backend

Use \`kubectl apply -f .\` inside this folder to deploy locally with minikube or another cluster.
EOF

