"""
JERP 2.0 - Compliance Pydantic Schemas
Request/Response schemas for compliance API endpoints
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.compliance_violation import (
    ViolationType,
    ViolationSeverity,
    ViolationStatus,
    RegulationType,
)


# ============================================================================
# Compliance Violation Schemas
# ============================================================================

class ComplianceViolationBase(BaseModel):
    """Base schema for compliance violation"""
    violation_type: ViolationType
    regulation: str = Field(..., max_length=255)
    severity: ViolationSeverity
    description: str
    entity_type: str = Field(..., max_length=100)
    entity_id: Optional[int] = None
    financial_impact: Optional[Decimal] = Field(None, decimal_places=2)
    metadata: Optional[Dict[str, Any]] = None


class ComplianceViolationCreate(ComplianceViolationBase):
    """Schema for creating a new compliance violation"""
    assigned_to: Optional[int] = None


class ComplianceViolationUpdate(BaseModel):
    """Schema for updating a compliance violation"""
    severity: Optional[ViolationSeverity] = None
    description: Optional[str] = None
    status: Optional[ViolationStatus] = None
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None
    financial_impact: Optional[Decimal] = Field(None, decimal_places=2)
    metadata: Optional[Dict[str, Any]] = None


class ComplianceViolationResolve(BaseModel):
    """Schema for resolving a violation"""
    resolution_notes: str = Field(..., min_length=10)


class ComplianceViolationResponse(ComplianceViolationBase):
    """Schema for compliance violation response"""
    id: int
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[int] = None
    status: ViolationStatus
    audit_log_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Compliance Rule Schemas
# ============================================================================

class ComplianceRuleBase(BaseModel):
    """Base schema for compliance rule"""
    rule_code: str = Field(..., max_length=100)
    rule_name: str = Field(..., max_length=255)
    description: str
    regulation_type: RegulationType
    severity: ViolationSeverity
    is_active: bool = True
    validation_logic: Optional[Dict[str, Any]] = None


class ComplianceRuleCreate(ComplianceRuleBase):
    """Schema for creating a compliance rule"""
    pass


class ComplianceRuleUpdate(BaseModel):
    """Schema for updating a compliance rule"""
    rule_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    severity: Optional[ViolationSeverity] = None
    is_active: Optional[bool] = None
    validation_logic: Optional[Dict[str, Any]] = None


class ComplianceRuleResponse(ComplianceRuleBase):
    """Schema for compliance rule response"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Compliance Report Schemas
# ============================================================================

class ComplianceReportCreate(BaseModel):
    """Schema for creating a compliance report"""
    report_type: str = Field(..., max_length=100)
    start_date: date
    end_date: date


class ComplianceReportResponse(BaseModel):
    """Schema for compliance report response"""
    id: int
    report_type: str
    start_date: date
    end_date: date
    total_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    generated_by: int
    generated_at: datetime
    report_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Statistics and Dashboard Schemas
# ============================================================================

class ViolationStatistics(BaseModel):
    """Violation statistics schema"""
    total_violations: int = 0
    open_violations: int = 0
    in_progress_violations: int = 0
    resolved_violations: int = 0
    dismissed_violations: int = 0
    critical_violations: int = 0
    high_violations: int = 0
    medium_violations: int = 0
    low_violations: int = 0
    labor_law_violations: int = 0
    financial_violations: int = 0
    other_violations: int = 0
    total_financial_impact: Decimal = Decimal("0.00")


class ViolationTrend(BaseModel):
    """Violation trend data point"""
    date: date
    count: int
    severity_breakdown: Dict[str, int] = {}


class ComplianceDashboardResponse(BaseModel):
    """Schema for compliance dashboard data"""
    statistics: ViolationStatistics
    recent_violations: List[ComplianceViolationResponse]
    trends: List[ViolationTrend]
    top_violation_types: Dict[str, int]
    compliance_score: float = Field(..., ge=0, le=100)


# ============================================================================
# Filter Schemas
# ============================================================================

class ComplianceViolationFilter(BaseModel):
    """Schema for filtering violations"""
    violation_type: Optional[ViolationType] = None
    severity: Optional[ViolationSeverity] = None
    status: Optional[ViolationStatus] = None
    entity_type: Optional[str] = None
    assigned_to: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# ============================================================================
# Validation Request/Response Schemas
# ============================================================================

class TimesheetValidationRequest(BaseModel):
    """Schema for timesheet validation request"""
    timesheet_id: int
    check_california_labor: bool = True
    check_flsa: bool = True


class TimesheetValidationResponse(BaseModel):
    """Schema for timesheet validation response"""
    timesheet_id: int
    is_compliant: bool
    violations: List[ComplianceViolationResponse]
    warnings: List[str] = []


class TransactionValidationRequest(BaseModel):
    """Schema for financial transaction validation request"""
    transaction_id: int
    check_gaap: bool = True
    check_ifrs: bool = False


class TransactionValidationResponse(BaseModel):
    """Schema for transaction validation response"""
    transaction_id: int
    is_compliant: bool
    violations: List[ComplianceViolationResponse]
    warnings: List[str] = []
