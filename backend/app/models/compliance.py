"""
JERP 2.0 - Compliance Models
Database models for compliance violation tracking and rule management
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ComplianceViolation(Base):
    """Track all compliance violations"""
    __tablename__ = "compliance_violations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    violation_type = Column(String(50), nullable=False, index=True)  # LABOR_LAW, GAAP, IFRS
    severity = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    standard = Column(String(100), nullable=False, index=True)  # e.g., "CA_LABOR_CODE_512", "GAAP_ASC_606"
    resource_type = Column(String(100), nullable=False, index=True)  # e.g., "payroll_entry", "journal_entry"
    resource_id = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    financial_impact = Column(DECIMAL(15, 2), nullable=True)
    
    def __repr__(self):
        return f"<ComplianceViolation(id={self.id}, type='{self.violation_type}', severity='{self.severity}')>"


class ComplianceRule(Base):
    """Store configurable compliance rules"""
    __tablename__ = "compliance_rules"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_code = Column(String(100), unique=True, nullable=False, index=True)
    rule_type = Column(String(50), nullable=False, index=True)  # LABOR, FINANCIAL
    standard = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    parameters = Column(JSON, nullable=True)  # Store rule-specific parameters
    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ComplianceRule(id={self.id}, code='{self.rule_code}', type='{self.rule_type}')>"


class ComplianceCheckLog(Base):
    """Log all compliance checks performed"""
    __tablename__ = "compliance_check_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    check_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=False, index=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    violations_found = Column(Integer, default=0, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User")
    
    def __repr__(self):
        return f"<ComplianceCheckLog(id={self.id}, type='{self.check_type}', passed={self.passed})>"
