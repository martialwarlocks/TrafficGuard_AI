# TrafficGuard AI

**Confident Enforcement. Humble Flagging.**

A next-generation uncertainty-aware traffic violation detection platform combining computer vision, explainable AI, human review workflows, and smart city analytics.

## Quick Start

```bash
# Clone and configure
cp .env.example .env

# Start all services
docker compose up -d

# Access
# Frontend:  http://localhost:5173
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
# MinIO:     http://localhost:9001
```

**Default login:** `admin@trafficguard.ai` / `admin123`

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Cameras   │────▶│  FastAPI     │────▶│  PostgreSQL     │
│  RTSP/USB   │     │  Backend     │     │  Structured DB  │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────────┐
                    │  ML Pipeline │────▶│  MinIO          │
                    │  YOLO+OCR    │     │  Evidence Store │
                    └──────┬───────┘     └─────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        Auto Process  Human Review  Discard
         (≥85%)       (60-84%)      (<60%)
```

## Core Innovation

### Uncertainty-Aware Routing
- **≥85% confidence** → Auto Process
- **60-84% confidence** → Human Review
- **<60% confidence** → Discard

### Explainable AI
Every decision includes natural-language reasoning:
- Helmet partially occluded
- Motion blur detected
- OCR disagreement
- Poor lighting / Low image quality

### Continuous Learning
Officer feedback (approve/reject/correct) feeds back into model retraining.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React, TypeScript, Vite, TailwindCSS, Framer Motion, Zustand, React Query, Recharts, Mapbox |
| Backend | FastAPI, SQLAlchemy, Alembic, Celery, Redis, JWT |
| AI/ML | YOLOv8s, PaddleOCR, OpenCV, PyTorch, MC Dropout, CLAHE |
| Storage | PostgreSQL, MinIO, Elasticsearch, Redis |
| DevOps | Docker, Docker Compose, Kubernetes, GitHub Actions |

## Project Structure

```
trafficguard-ai/
├── frontend/          # React command-center UI
├── backend/           # FastAPI REST API
├── ml/                # AI pipeline & violation modules
│   ├── pipeline/      # Quality, detection, OCR, uncertainty
│   └── violations/    # Helmet, seatbelt, triple riding, etc.
├── scripts/           # Dataset & training scripts
├── deployment/        # Docker, K8s, NGINX configs
└── docs/              # Architecture, pitch, deployment guides
```

## AI Pipeline

1. **Image Quality Assessment** — blur, brightness, noise, contrast
2. **Image Enhancement** — CLAHE, denoising, sharpening
3. **Detection** — YOLOv8s (vehicles, helmets, plates, seatbelts)
4. **OCR** — PaddleOCR license plate recognition
5. **Uncertainty Estimation** — MC Dropout (20 passes)
6. **Routing** — confidence-based decision engine
7. **Explainability** — natural-language reason generation

### Confidence Formula

```
final_confidence = 0.5 × model_confidence
                 + 0.2 × quality_score
                 + 0.2 × stability_score
                 + 0.1 × ocr_confidence
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | JWT authentication |
| POST | `/api/v1/upload` | Upload & analyze media |
| POST | `/api/v1/analyze` | Analyze image |
| GET | `/api/v1/violations` | List violations |
| GET | `/api/v1/review-queue` | Human review queue |
| POST | `/api/v1/review` | Submit review decision |
| GET | `/api/v1/analytics` | Smart city analytics |
| GET | `/api/v1/heatmap` | Violation heatmap |
| GET | `/api/v1/cameras` | Camera management |
| GET | `/api/v1/evidence/{id}` | Evidence viewer |
| GET | `/api/v1/model-metrics` | Model monitoring |
| POST | `/api/v1/feedback` | Officer feedback |
| GET | `/api/v1/health` | System health |

## Development

```bash
# Backend
cd trafficguard-ai
pip install -r backend/requirements.txt
PYTHONPATH=. uvicorn backend.app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# ML Training
python scripts/download_datasets.py
python scripts/prepare_datasets.py
python scripts/train_yolo.py
python scripts/evaluate_model.py
```

## License

MIT
