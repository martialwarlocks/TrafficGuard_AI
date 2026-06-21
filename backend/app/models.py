import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer,
    String, Text, JSON, Table, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    OFFICER = "officer"
    ANALYST = "analyst"


class ViolationType(str, enum.Enum):
    HELMET = "helmet"
    SEATBELT = "seatbelt"
    TRIPLE_RIDING = "triple_riding"
    RED_LIGHT = "red_light"
    WRONG_SIDE = "wrong_side"
    STOP_LINE = "stop_line"
    PARKING = "parking"


class RoutingDecision(str, enum.Enum):
    AUTO_PROCESS = "auto_process"
    HUMAN_REVIEW = "human_review"
    DISCARD = "discard"


class ReviewAction(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"


class CameraStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String(500))
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    reviews = relationship("Review", back_populates="officer")
    audit_logs = relationship("AuditLog", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    camera_id = Column(String(100), unique=True, index=True, nullable=False)
    stream_url = Column(String(500))
    stream_type = Column(String(50), default="rtsp")
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String(255))
    status = Column(Enum(CameraStatus), default=CameraStatus.OFFLINE)
    is_active = Column(Boolean, default=True)
    fps = Column(Float, default=30.0)
    resolution = Column(String(20), default="1920x1080")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    violations = relationship("Violation", back_populates="camera")


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    violation_type = Column(Enum(ViolationType), nullable=False, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), index=True)
    vehicle_type = Column(String(50))
    plate_number = Column(String(20), index=True)
    confidence = Column(Float, nullable=False)
    uncertainty = Column(Float, nullable=False)
    model_confidence = Column(Float)
    quality_score = Column(Float)
    stability_score = Column(Float)
    ocr_confidence = Column(Float)
    routing_decision = Column(Enum(RoutingDecision), nullable=False, index=True)
    routing_rationale = Column(Text)
    explanation = Column(JSON)
    status = Column(String(50), default="pending", index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    fine_amount = Column(Float, default=0.0)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    camera = relationship("Camera", back_populates="violations")
    evidence = relationship("Evidence", back_populates="violation", uselist=False)
    reviews = relationship("Review", back_populates="violation")
    feedback = relationship("Feedback", back_populates="violation")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), unique=True, nullable=False)
    original_image_path = Column(String(500), nullable=False)
    enhanced_image_path = Column(String(500))
    annotated_image_path = Column(String(500))
    video_path = Column(String(500))
    ocr_result = Column(String(20))
    ocr_confidence = Column(Float)
    ocr_alternatives = Column(JSON)
    evidence_hash = Column(String(64), nullable=False, index=True)
    integrity_status = Column(String(50), default="verified")
    quality_metrics = Column(JSON)
    detection_data = Column(JSON)
    chain_of_custody = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    violation = relationship("Violation", back_populates="evidence")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False, index=True)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(Enum(ReviewAction), nullable=False)
    notes = Column(Text)
    review_duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    violation = relationship("Violation", back_populates="reviews")
    officer = relationship("User", back_populates="reviews")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    corrected_label = Column(String(50))
    notes = Column(Text)
    used_for_training = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    violation = relationship("Violation", back_populates="feedback")
    user = relationship("User", back_populates="feedback")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False)
    precision = Column(Float)
    recall = Column(Float)
    map50 = Column(Float)
    map50_95 = Column(Float)
    f1_score = Column(Float)
    avg_confidence = Column(Float)
    avg_uncertainty = Column(Float)
    latency_ms = Column(Float)
    fps = Column(Float)
    gpu_utilization = Column(Float)
    drift_score = Column(Float)
    retraining_status = Column(String(50), default="idle")
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    active_cameras = Column(Integer)
    queue_depth = Column(Integer)
    requests_per_minute = Column(Float)
    error_rate = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    condition = Column(JSON, nullable=False)
    severity = Column(String(20), default="warning")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ThresholdConfig(Base):
    __tablename__ = "threshold_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    auto_process_threshold = Column(Float, default=0.85)
    human_review_threshold = Column(Float, default=0.60)
    quality_min_threshold = Column(Float, default=0.40)
    updated_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
