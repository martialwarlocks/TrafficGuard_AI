# TrafficGuard AI — Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- 8GB RAM minimum (16GB recommended for ML inference)
- NVIDIA GPU optional (CPU inference supported)

## Quick Deploy (Docker Compose)

```bash
git clone <repo-url> trafficguard-ai
cd trafficguard-ai
cp .env.example .env
docker compose up -d
```

Services started:
| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 5173 | React UI |
| Backend | 8000 | FastAPI API |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & queues |
| MinIO | 9000/9001 | Object storage |
| Elasticsearch | 9200 | Search & analytics |
| NGINX | 80 | Reverse proxy |

## Production Deployment (Kubernetes)

```bash
# Create namespace and secrets
kubectl create namespace trafficguard
kubectl create secret generic trafficguard-secrets \
  --from-env-file=.env -n trafficguard

# Deploy
kubectl apply -f deployment/kubernetes/deployment.yaml

# Verify
kubectl get pods -n trafficguard
kubectl get svc -n trafficguard
```

## Environment Variables

See `.env.example` for all configuration options. Critical production settings:

```bash
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
POSTGRES_PASSWORD=<strong-password>
MINIO_SECRET_KEY=<strong-password>
DEBUG=false
APP_ENV=production
```

## ML Model Setup

```bash
# Download base YOLOv8s (auto-downloaded on first inference)
mkdir -p ml/models

# Optional: Train custom model
python scripts/download_datasets.py --dataset helmet
python scripts/prepare_datasets.py
python scripts/train_yolo.py --epochs 100
python scripts/evaluate_model.py
```

## Database Migrations

```bash
cd backend
PYTHONPATH=.. alembic upgrade head
```

## Health Checks

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/docs
```

## Monitoring

- System metrics collected every 60 seconds via Celery Beat
- Model drift checked hourly
- Health endpoint reports status of all dependencies

## Backup

```bash
# PostgreSQL
docker exec tg-postgres pg_dump -U trafficguard trafficguard > backup.sql

# MinIO evidence
docker exec tg-minio mc mirror /data/trafficguard-evidence ./evidence-backup
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ML model slow on first run | YOLOv8 downloads weights on first inference (~22MB) |
| PaddleOCR install fails | Use CPU version: `pip install paddlepaddle` |
| Frontend can't reach API | Check CORS_ORIGINS in .env |
| Celery tasks not processing | Verify Redis is running and CELERY_BROKER_URL is correct |
