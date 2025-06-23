#!/bin/bash
set -e

# Start FastAPI in the background
uvicorn app:app --host 0.0.0.0 --port 8000 --reload &

# Start flush worker in the foreground (keeps container alive)
python flush_worker.py
