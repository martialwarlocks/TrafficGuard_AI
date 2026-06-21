#!/bin/bash
set -e

echo "🚀 Starting TrafficGuard AI..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env from template"
fi

echo "🐳 Starting Docker services..."
docker compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

echo "✅ TrafficGuard AI is running!"
echo ""
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  MinIO:     http://localhost:9001"
echo ""
echo "  Login: admin@trafficguard.ai / admin123"
echo ""
