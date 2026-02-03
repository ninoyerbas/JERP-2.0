"""
JERP 2.0 - Compliance Models
Database models for compliance tracking and violations
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum, Numeric, Boolean, Date
from sqlalchemy.orm import relationship
from enum import Enum
from app.core.database import Base


class ViolationType(str, Enum):
    """Types of compliance violations"""
    LABOR_LAW = "LABOR_LAW"
    FINANCIAL = "FINANCIAL"
    OTHER = "OTHER"


class ViolationSeverity(str, Enum):
    """Severity levels for violations"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ViolationStatus(str, Enum):
    """Status of violation resolution"""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class RegulationType(str, Enum):
    """Types of regulations"""
    CALIFORNIA_LABOR = "CALIFORNIA_LABOR"
    FLSA = "FLSA"
    GAAP = "GAAP"
    IFRS = "IFRS"
    OTHER = "OTHER"


class ComplianceViolation(Base):
    """
    Compliance violation tracking with audit trail integration.
    Tracks labor law and financial compliance violations.
    """
    __tablename__ = "compliance_violations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Violation classification
    violation_type = Column(SQLEnum(ViolationType), nullable=False, index=True)
    regulation = Column(String(255), nullable=False, index=True)
    severity = Column(SQLEnum(ViolationSeverity), nullable=False, index=True)
    
    # Violation details
    description = Column(Text, nullable=False)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True, index=True)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution tracking
    resolution_notes = Column(Text, nullable=True)
    financial_impact = Column(Numeric(15, 2), nullable=True)
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    
    # Status tracking
    status = Column(SQLEnum(ViolationStatus), default=ViolationStatus.OPEN, nullable=False, index=True)
    
    # Audit trail integration
    audit_log_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=True)
    audit_log = relationship("AuditLog", foreign_keys=[audit_log_id])
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<ComplianceViolation(id={self.id}, type='{self.violation_type}', severity='{self.severity}')>"


class ComplianceRule(Base):
    """
    Compliance rule definitions for automated checking.
    Stores rules that can be dynamically evaluated.
    """
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Rule identification
    rule_code = Column(String(100), unique=True, nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Rule classification
    regulation_type = Column(SQLEnum(RegulationType), nullable=False, index=True)
    severity = Column(SQLEnum(ViolationSeverity), nullable=False)
    
    # Rule status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Dynamic validation logic (JSON-encoded)
    validation_logic = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ComplianceRule(id={self.id}, code='{self.rule_code}', type='{self.regulation_type}')>"


class ComplianceReport(Base):
    """
    Generated compliance reports for auditing and tracking.
    Stores aggregated compliance data over time periods.
    """
    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Report details
    report_type = Column(String(100), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    
    # Violation counts
    total_violations = Column(Integer, default=0, nullable=False)
    critical_violations = Column(Integer, default=0, nullable=False)
    high_violations = Column(Integer, default=0, nullable=False)
    medium_violations = Column(Integer, default=0, nullable=False)
    low_violations = Column(Integer, default=0, nullable=False)
    
    # Report metadata
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    generated_user = relationship("User", foreign_keys=[generated_by])
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Report data (JSON-encoded detailed information)
    report_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<ComplianceReport(id={self.id}, type='{self.report_type}', period={self.start_date} to {self.end_date})>"
