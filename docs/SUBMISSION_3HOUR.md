# 3-Hour Submission Sprint

**Forget training. Ship the demo judges can see and trust.**

---

## Hour 1 — Get It Running (0:00–1:00)

### 0–10 min: Infrastructure

```bash
cd trafficguard-ai
docker compose up -d postgres redis minio
# Wait ~30s for postgres
```

If port 5432 is busy, use local `.env`:
```
DATABASE_URL=postgresql+asyncpg://trafficguard:trafficguard_secret@localhost:5433/trafficguard
```
(Postgres mapped to 5433 in docker-compose if needed.)

### 10–25 min: Backend + Frontend

```bash
# Terminal 1 — backend
source .venv/bin/activate   # or: python -m venv .venv && pip install -r backend/requirements.txt
export PYTHONPATH=/Users/yatins/flipkart/trafficguard-ai
# Speed up live webcam (critical for demo):
export MC_DROPOUT_PASSES=5
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 — login `admin@trafficguard.ai` / `admin123`

### 25–45 min: Smoke test (do NOT skip)

| Step | Page | Pass? |
|------|------|-------|
| 1 | Dashboard loads with KPIs | ☐ |
| 2 | Live Monitoring → upload ANY traffic photo | ☐ |
| 3 | Red-light photo → shows **red light** (not seatbelt) | ☐ |
| 4 | **Webcam Test** → Start → frame scans every 2.5s | ☐ |
| 5 | Human Review shows uploaded case | ☐ |
| 6 | Analytics chart has data after 3+ uploads | ☐ |

**If webcam is slow:** set `MC_DROPOUT_PASSES=3` in `.env`, restart backend.

### 45–60 min: Pre-seed dashboard

Upload **5 images** via Live Monitoring (reuse same photos is fine):
1. Red-light violation photo (your best one)
2. Motorcycle / helmet scene
3. Car interior / seatbelt scene
4. Busy intersection (may route to review — good!)
5. Any traffic scene

Goal: Dashboard trends + Review queue look alive.

---

## Hour 2 — Demo + Video (1:00–2:00)

### 1:00–1:20: Rehearse this exact 3-minute flow

**0:00–0:30 Problem**
> "AI traffic cameras fine people at 62% confidence. One wrong ticket destroys public trust."

**0:30–1:30 LIVE WEBCAM (your wow moment)**
- Go to **Webcam Test** → Start Live Test
- Hold red-light violation photo steady for 3 seconds
- Point at: SIGNAL badge, confidence %, routing decision
- Say: *"Real inference every 2.5 seconds — not a pre-recorded video."*

**1:30–2:15 Human Review**
- Open case from queue → side-by-side evidence
- Show explainability: "Helmet occluded" / "Signal RED detected"
- Approve or reject — *"Borderline cases never auto-fine."*

**2:15–3:00 Dashboard close**
> "Confident enforcement for clear cases. Humble flagging for borderline ones."

### 1:20–1:50: Record backup video

Use QuickTime / OBS / phone:
- 60–90 seconds max
- Screen record: login → Webcam Test → one violation hit → Review queue
- Upload to YouTube (unlisted) or Google Drive — **submission link ready**

### 1:50–2:00: Screenshot pack (for PDF/slides)

Capture 4 screenshots:
1. Landing page tagline
2. Webcam Test with annotated overlay
3. Human Review with evidence images
4. Dashboard with violation trends

---

## Hour 3 — Submit (2:00–3:00)

### 2:00–2:20: GitHub push

```bash
git add -A
git commit -m "Add live webcam demo and hackathon submission polish"
git push origin main
```

Repo: https://github.com/martialwarlocks/TrafficGuard_AI

### 2:20–2:40: Write submission text (copy-paste ready)

**Project name:** TrafficGuard AI

**Tagline:** Confident Enforcement. Humble Flagging.

**One-liner:**
Uncertainty-aware traffic violation detection — auto-process high confidence, human-review borderline, discard low confidence. Live webcam demo included.

**Problem:** AI enforcement at arbitrary confidence creates false fines and legal risk.

**Solution:** MC Dropout uncertainty routing + explainable AI + officer review workflow + smart city dashboard.

**Tech:** YOLOv8s, PaddleOCR, FastAPI, React, PostgreSQL, MinIO, Docker.

**Demo URL:** http://localhost:5173 (or your deployed URL)
**Video:** [your YouTube/Drive link]
**Repo:** https://github.com/martialwarlocks/TrafficGuard_AI

**Login:** admin@trafficguard.ai / admin123

### 2:40–2:55: Final checklist

- [ ] GitHub repo public and README has Quick Start
- [ ] Demo video uploaded (unlisted link works)
- [ ] 3+ violations in dashboard
- [ ] Webcam demo tested once more
- [ ] Laptop charged, backend + frontend terminals bookmarked
- [ ] Red-light test photo saved on desktop for quick access

### 2:55–3:00: Submit

Hit submit. You're done.

---

## If Something Breaks (5-min fixes)

| Problem | Fix |
|---------|-----|
| Backend won't start | Check `PYTHONPATH=.` and postgres on 5433 |
| Webcam permission denied | Use Chrome, allow camera, use HTTPS or localhost |
| Analysis timeout | `MC_DROPOUT_PASSES=3`, restart backend |
| Wrong violation type | Use red-light photo; show Review queue if borderline |
| Empty dashboard | Upload 3 images via Live Monitoring |
| Docker fails | Run postgres/redis/minio only; backend locally |

---

## What NOT to do in 3 hours

- ❌ Train YOLO (takes 4+ hours)
- ❌ Rewrite architecture
- ❌ Deploy to cloud (unless already set up)
- ❌ Add new violation types

## What WILL impress judges

- ✅ Live webcam (almost no team has this)
- ✅ Human review workflow (shows you thought about liability)
- ✅ Plain-English explainability panel
- ✅ Polished dashboard with real uploaded data
- ✅ Clear pitch: "We know when NOT to enforce"

**Win by being the only team that routes by confidence band.**
