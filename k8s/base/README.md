# Kubernetes Base Manifests

This folder contains the Kubernetes YAML manifests for:

-  – Defines the `search-logger` namespace
-  – PostgreSQL deployment and service
-  – Redis deployment and service
-  – Grafana deployment and service
-  – Go backend
-  – Python backend
-  – Elixir backend

Use `kubectl apply -f .` inside this folder to deploy locally with minikube or another cluster.
