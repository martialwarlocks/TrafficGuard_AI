# TrafficGuard AI — Database Schema

## Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ reviews : performs
    users }o--|| roles : has
    roles ||--o{ permissions : grants
    cameras ||--o{ violations : captures
    violations ||--|| evidence : has
    violations ||--o{ reviews : receives
    violations ||--o{ feedback : generates
    users ||--o{ audit_logs : creates
    users ||--o{ feedback : submits

    users {
        int id PK
        string email UK
        string hashed_password
        string full_name
        int role_id FK
        boolean is_active
        datetime created_at
    }

    roles {
        int id PK
        string name UK
        string description
    }

    cameras {
        int id PK
        string camera_id UK
        string name
        string stream_url
        float latitude
        float longitude
        enum status
    }

    violations {
        int id PK
        enum violation_type
        int camera_id FK
        float confidence
        float uncertainty
        enum routing_decision
        json explanation
        string status
        datetime detected_at
    }

    evidence {
        int id PK
        int violation_id FK UK
        string original_image_path
        string enhanced_image_path
        string annotated_image_path
        string evidence_hash
        json chain_of_custody
        string integrity_status
    }

    reviews {
        int id PK
        int violation_id FK
        int officer_id FK
        enum action
        text notes
        datetime created_at
    }

    feedback {
        int id PK
        int violation_id FK
        int user_id FK
        boolean is_correct
        string corrected_label
    }

    audit_logs {
        int id PK
        int user_id FK
        string action
        string resource_type
        json details
        datetime created_at
    }

    model_metrics {
        int id PK
        string model_version
        float precision
        float recall
        float map50
        float f1_score
        datetime recorded_at
    }
```

## Key Tables

| Table | Records | Purpose |
|-------|---------|---------|
| users | Officers, admins, analysts | Authentication & RBAC |
| violations | Detection results | Core enforcement records |
| evidence | Images, hashes, custody | Forensic evidence chain |
| reviews | Officer decisions | Human-in-the-loop audit trail |
| feedback | Corrections | Continuous learning input |
| audit_logs | All actions | Compliance & security |
| model_metrics | Performance snapshots | Model monitoring & drift |

## Indexes

- `violations.violation_type` — filter by violation category
- `violations.routing_decision` — review queue queries
- `violations.detected_at` — time-range analytics
- `violations.plate_number` — plate lookup
- `evidence.evidence_hash` — integrity verification
