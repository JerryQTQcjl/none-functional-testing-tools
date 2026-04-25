#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

WORKERS=${1:-3}

echo "========================================"
echo "  LoadForge 压测平台 - Quick Start"
echo "========================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose v2 is not available"
    exit 1
fi

echo "Setting worker count to: $WORKERS"
export WORKER_COUNT=$WORKERS

echo ""
echo "Building images..."
docker compose build

echo ""
echo "Starting services..."
docker compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "========================================"
echo "  LoadForge is starting!"
echo "========================================"
echo ""
echo "  Web Console:   http://localhost:3000"
echo "  API Server:    http://localhost:${MASTER_PORT:-8000}"
echo "  Demo Target:   http://localhost:8080"
echo "  Redis:         localhost:6379"
echo ""
echo "  Workers: $WORKERS"
echo ""
echo "  Scale workers: docker compose up -d --scale worker=N"
echo "  Stop:          docker compose down"
echo "========================================"
