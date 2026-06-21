# TrafficGuard AI — Judge Demo Script

## Pre-Demo Setup (5 minutes before)

1. `docker compose up -d` — start all services
2. Open http://localhost:5173 — landing page
3. Login: `admin@trafficguard.ai` / `admin123`
4. Prepare a traffic violation test image (motorcycle without helmet)

---

## Demo Flow (5 minutes)

### Act 1: The Problem (30 seconds)
> "Current traffic AI systems generate a confidence score and enforce anyway. They can't distinguish between a reliable detection and a legally risky borderline case. One false positive erodes public trust for years."

### Act 2: Landing Page (30 seconds)
- Show premium landing page with tagline: **Confident Enforcement. Humble Flagging.**
- Point out the three core innovations: Uncertainty Routing, Explainable AI, Officer Feedback Loop
- Click **Launch Dashboard**

### Act 3: Command Center (45 seconds)
- Walk through KPI cards: violations, auto-processed, human reviewed, pending reviews
- Highlight **Average Confidence** vs **Average Uncertainty** metrics
- Show system health and recent activity feed
- "This is a live command center, not a static dashboard."

### Act 4: Live Monitoring — THE WOW MOMENT (90 seconds)
- Navigate to **Live Monitoring**
- Upload a test image with a traffic violation
- Watch real YOLOv8 inference run (actual model, not mocked)
- Point out:
  - Animated detection bounding boxes
  - Confidence gauge (e.g., 72%)
  - Uncertainty gauge (e.g., 28%)
  - **AI Copilot panel** explaining WHY: "Helmet partially occluded", "Low image quality"
  - Routing decision: **HUMAN REVIEW** (because 72% is in the 60-84% band)

### Act 5: Human Review Workflow (60 seconds)
- Navigate to **Human Review**
- Show the flagged violation in the review queue
- Display original/enhanced/annotated images side by side
- Show explainability cards with uncertainty reasons
- Click **Approve** or **Reject** — action stored in audit log
- "Every borderline case gets human oversight. High confidence auto-processes. Low confidence is discarded."

### Act 6: Evidence & Analytics (45 seconds)
- Quick tour of **Evidence Viewer** — SHA256 hash, chain of custody, integrity status
- Show **Analytics** — violation heatmap, confidence/uncertainty distributions, model drift
- Show **Digital Twin** — camera map with violation density

### Act 7: Close (30 seconds)
> "TrafficGuard AI doesn't just detect violations — it knows when it's unsure, explains why, and routes accordingly. Confident enforcement for clear cases. Humble flagging for borderline ones. That's how you build public trust in AI enforcement."

---

## Backup Talking Points

- **Real inference**: YOLOv8s + PaddleOCR, not mocked detections
- **MC Dropout**: 20 stochastic passes for uncertainty quantification
- **Confidence formula**: weighted combination of model, quality, stability, OCR
- **Continuous learning**: officer feedback feeds model retraining pipeline
- **Production-ready**: Docker Compose, Kubernetes, CI/CD, full API documentation

## Expected Judge Questions

See `docs/FAQ.md` for prepared answers.
