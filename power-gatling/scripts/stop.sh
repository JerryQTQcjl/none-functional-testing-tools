#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "Stopping LoadForge..."
docker compose down

echo ""
echo "LoadForge stopped. To remove volumes: docker compose down -v"
