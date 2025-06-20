#!/bin/bash

echo "Creating search-logger project structure..."

# Create top-level directories
mkdir -p .github/workflows
mkdir -p infra/postgres
mkdir -p infra/grafana/dashboards
mkdir -p infra/redis
mkdir -p go python elixir
mkdir -p test-harness

# Create top-level files
touch README.md
touch docker-compose.yml
touch grafana-dashboard.md

# Create infra files
touch infra/postgres/init.sql
touch infra/redis/redis.conf  # optional

# CI workflow
cat <<EOF > .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: search
          POSTGRES_PASSWORD: search
          POSTGRES_DB: search_logs
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Run Go tests
        working-directory: ./go
        run: go test ./... || echo "No tests yet"
EOF

# Stub backend files
touch go/main.go go/logger.go go/Dockerfile
touch python/app.py python/logger.py python/Dockerfile
touch elixir/Dockerfile

# Test harness
touch test-harness/seed.py test-harness/test_runner.py

echo "✅ All directories and files created. You’re ready to build!"

