#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

COUNT=${1:-3}

echo "Scaling workers to $COUNT..."
docker compose up -d --scale worker=$COUNT --no-recreate

echo ""
echo "Current worker count: $COUNT"
echo "Check status: docker compose ps worker"
