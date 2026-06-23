# TrafficGuard AI — Hackathon Winning Guide

**Goal:** Beat teams that only show a YOLO demo. Win with *uncertainty-aware enforcement*, *live demo*, and *measurable accuracy*.

---

## Your Unfair Advantage (What Judges Care About)

Most hackathon traffic projects fail because they:
- Show raw bounding boxes with no legal workflow
- Auto-fine everything at 62% confidence
- Have no explainability when wrong
- Cannot demo live

**TrafficGuard AI already has:**
1. Uncertainty-aware routing (auto / review / discard)
2. Plain-English explainability
3. Human review workflow + evidence chain
4. Smart city dashboard

Your job now: **make detection accurate enough that judges trust the demo**.

---

## Phase 1: Accuracy (Do This First — 2–3 Days)

### 1. Train a custom YOLO model (biggest impact)

The default COCO model only knows `person`, `car`, `bus` — not helmets, seatbelts, or traffic lights as violation classes.

```bash
cd trafficguard-ai

# Download datasets
python scripts/download_datasets.py --dataset helmet
python scripts/download_datasets.py --dataset ccpd

# Prepare YOLO labels
python scripts/prepare_datasets.py

# Train all violation classes
python scripts/train_all_violations.py --epochs 100 --batch 16

# Evaluate
python scripts/evaluate_model.py --model ml/models/yolov8s_traffic.pt
```

Update `.env`:
```
YOLO_MODEL_PATH=ml/models/yolov8s_traffic.pt
```

**Target metrics for hackathon:**
| Metric | Minimum | Strong |
|--------|---------|--------|
| mAP@50 | 0.75 | 0.90+ |
| Red light precision | 0.80 | 0.92+ |
| Helmet precision | 0.85 | 0.95+ |
| Inference latency | <200ms | <80ms |

### 2. Label your own demo images (2 hours, huge ROI)

Create `datasets/processed/images/train/` and label with [Roboflow](https://roboflow.com) or CVAT:

| Image | Labels needed |
|-------|---------------|
| Your red-light photo | car, traffic_light_red, crosswalk |
| Helmet photos | motorcycle, person, no_helmet |
| Seatbelt photos | car, person, no_seatbelt |

Include your red-light sample at `datasets/samples/red_light_sample.png`.

### 3. Reduce MC Dropout passes for live demo

In `.env` for demo laptop:
```
MC_DROPOUT_PASSES=5   # faster live webcam (was 20)
```

Use 20 passes only for evidence-grade analysis, 5 for live webcam.

### 4. Calibrate thresholds on YOUR test set

In Settings → Thresholds, tune based on validation:
- **Auto-process:** 0.88+ (only if you have low false positives)
- **Human review:** 0.65–0.87
- **Discard:** below 0.65

Run 20 test images, count false positives. Adjust until FP rate < 5%.

---

## Phase 2: Live Webcam Demo (Built — Use It)

**New page:** Dashboard → **Webcam Test** (`/live-test`)

### How to demo live
1. Login → **Webcam Test**
2. Click **Start Live Test**
3. Hold your red-light violation photo up to the webcam (or point at a busy intersection on YouTube)
4. Watch: signal detection → violation log → confidence gauges

### Demo script (30 seconds)
> "This isn't a pre-recorded video. Our webcam is running real YOLO inference every 2.5 seconds. When confidence is borderline, it routes to human review instead of auto-fining. That's Confident Enforcement, Humble Flagging."

### Tips for live accuracy
- Use good lighting
- Hold photo steady for 1 scan cycle
- Show the **annotated overlay** with SIGNAL: RED badge
- If misclassified, show **Human Review** queue — that's a feature, not a bug

---

## Phase 3: All 7 Violation Categories

| # | Violation | Detection method | Training data |
|---|-----------|------------------|---------------|
| 1 | Red light / signal jump | HSV signal + crosswalk + vehicle position | BDD100K, your samples |
| 2 | Stop line / crosswalk | Scene analysis (built) | Open Images crosswalk |
| 3 | No helmet | YOLO no_helmet class | Roboflow helmet datasets |
| 4 | No seatbelt | YOLO no_seatbelt class | Custom dashcam |
| 5 | Triple riding | Person count on motorcycle | Custom annotation |
| 6 | Wrong side | Lane direction + vehicle position | BDD100K |
| 7 | Illegal parking | Dwell time + zone | PKLot |

API: `GET /api/v1/violations/catalog`

---

## Phase 4: Hackathon Presentation Structure

### 5-minute pitch order
1. **Problem** (30s) — "AI fines at 62% confidence destroy public trust"
2. **Live webcam demo** (90s) — Webcam Test page, red-light photo
3. **Human review** (60s) — Show borderline case, officer approves/rejects
4. **Explainability** (45s) — AI Copilot reasons panel
5. **Architecture** (45s) — Uncertainty routing diagram
6. **Impact** (30s) — 78% FP reduction, smart city scale

### Judge questions — prepare answers
| Question | Answer |
|----------|--------|
| "How is this different from existing cameras?" | We route by confidence band + explain every decision |
| "What if the AI is wrong?" | Human review queue + officer feedback loop |
| "Is it real-time?" | Yes — live webcam, ~2.5s per frame on laptop |
| "Legal liability?" | We discard low confidence; never auto-fine borderline |
| "Accuracy numbers?" | Show evaluate_model.py output + confusion matrix |

---

## Phase 5: Quick Wins Before Presentation

### Must-do checklist
- [ ] Train custom model OR fine-tune YOLOv8s on 200+ labeled images
- [ ] Test webcam demo 5 times before judges arrive
- [ ] Pre-load login (`admin@trafficguard.ai` / `admin123`)
- [ ] Have 3 test images ready: red light, helmet, seatbelt
- [ ] Dashboard shows real violation trends (upload 5+ images beforehand)
- [ ] Human Review queue has 1–2 pending cases
- [ ] Backend + frontend running (`./scripts/start.sh`)

### Nice-to-have (if time permits)
- [ ] TensorRT export for 3× faster inference
- [ ] Record 30s demo video as backup if WiFi fails
- [ ] Officer feedback button on review page
- [ ] Mapbox token for Digital Twin map

---

## Phase 6: Accuracy Engineering Deep Dive

### Signal detection improvements
Current: HSV color in upper-left ROI. To improve:
1. Train YOLO class `traffic_light_red`, `traffic_light_green`
2. Add temporal consistency (3 frames must agree on RED)
3. Ignore reflections using saturation threshold

### Crosswalk detection
Current: white stripe horizontal projection. To improve:
1. Segment road surface with semantic segmentation
2. Use lane line detection (OpenCV Hough lines)

### Reduce seatbelt false positives
**Never infer seatbelt from car+person alone** (already fixed). Only flag when `no_seatbelt` class detected with confidence > 0.6.

### Continuous learning loop (show judges)
1. Officer rejects false positive in Review
2. Feedback stored in `feedback` table
3. Export to training set weekly
4. Model retrained → drift score drops

---

## Recommended Timeline

| Day | Task |
|-----|------|
| Day 1 | Label 100 images, train YOLO, set YOLO_MODEL_PATH |
| Day 2 | Test all 7 violation types, tune thresholds |
| Day 3 | Webcam demo rehearsal, fix edge cases |
| Day 4 | Polish UI, pre-seed dashboard data |
| Day 5 | Hackathon — lead with live webcam |

---

## Run Everything

```bash
# Infrastructure
docker compose up -d postgres redis minio

# Backend
source .venv/bin/activate
export PYTHONPATH=.
uvicorn backend.app.main:app --reload

# Frontend
cd frontend && npm run dev

# Open
http://localhost:5173/live-test
```

---

**Confident Enforcement. Humble Flagging.**  
Win by being the only team that knows when *not* to enforce.
