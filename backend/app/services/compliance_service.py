"""
JERP 2.0 - Compliance Service
Business logic for compliance violation tracking and reporting
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.compliance_violation import (
    ComplianceViolation,
    ComplianceRule,
    ComplianceReport,
    ViolationType,
    ViolationSeverity,
    ViolationStatus,
    RegulationType,
)
from app.models.audit_log import AuditLog
from app.schemas.compliance import (
    ComplianceViolationCreate,
    ComplianceViolationUpdate,
    ComplianceViolationFilter,
    ComplianceReportCreate,
    ViolationStatistics,
)


class ComplianceService:
    """Service for managing compliance violations and reports"""
    
    def __init__(self, db: Session):
        """
        Initialize compliance service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_violation(
        self,
        violation_data: ComplianceViolationCreate,
        user_id: int,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ComplianceViolation:
        """
        Log a new compliance violation with audit trail.
        
        Args:
            violation_data: Violation data
            user_id: User creating the violation
            user_email: Email of user
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            Created ComplianceViolation
        """
        # Get previous audit log hash for chain
        last_audit = self.db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        previous_hash = last_audit.current_hash if last_audit else None
        
        # Create audit log entry
        audit_log = AuditLog.create_entry(
            user_id=user_id,
            user_email=user_email,
            action="CREATE_COMPLIANCE_VIOLATION",
            resource_type="compliance_violation",
            resource_id=None,  # Will be updated after violation is created
            old_values=None,
            new_values={
                "violation_type": violation_data.violation_type.value,
                "regulation": violation_data.regulation,
                "severity": violation_data.severity.value,
                "description": violation_data.description,
                "entity_type": violation_data.entity_type,
                "entity_id": violation_data.entity_id,
            },
            description=f"Compliance violation detected: {violation_data.regulation}",
            ip_address=ip_address,
            user_agent=user_agent,
            previous_hash=previous_hash
        )
        
        self.db.add(audit_log)
        self.db.flush()  # Get audit_log.id
        
        # Create violation
        violation = ComplianceViolation(
            violation_type=violation_data.violation_type,
            regulation=violation_data.regulation,
            severity=violation_data.severity,
            description=violation_data.description,
            entity_type=violation_data.entity_type,
            entity_id=violation_data.entity_id,
            financial_impact=violation_data.financial_impact,
            assigned_to=violation_data.assigned_to,
            status=ViolationStatus.OPEN,
            audit_log_id=audit_log.id,
            metadata=violation_data.metadata,
        )
        
        self.db.add(violation)
        self.db.commit()
        self.db.refresh(violation)
        
        # Update audit log with violation ID
        audit_log.resource_id = str(violation.id)
        self.db.commit()
        
        return violation
    
    def get_violations(
        self,
        filters: Optional[ComplianceViolationFilter] = None
    ) -> List[ComplianceViolation]:
        """
        Retrieve violations with optional filtering.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            List of ComplianceViolation objects
        """
        query = self.db.query(ComplianceViolation)
        
        if filters:
            if filters.violation_type:
                query = query.filter(ComplianceViolation.violation_type == filters.violation_type)
            
            if filters.severity:
                query = query.filter(ComplianceViolation.severity == filters.severity)
            
            if filters.status:
                query = query.filter(ComplianceViolation.status == filters.status)
            
            if filters.entity_type:
                query = query.filter(ComplianceViolation.entity_type == filters.entity_type)
            
            if filters.assigned_to:
                query = query.filter(ComplianceViolation.assigned_to == filters.assigned_to)
            
            if filters.start_date:
                query = query.filter(ComplianceViolation.detected_at >= filters.start_date)
            
            if filters.end_date:
                query = query.filter(ComplianceViolation.detected_at <= filters.end_date)
            
            # Apply pagination
            query = query.offset(filters.skip).limit(filters.limit)
        
        return query.order_by(ComplianceViolation.detected_at.desc()).all()
    
    def get_violation_by_id(self, violation_id: int) -> Optional[ComplianceViolation]:
        """
        Get a specific violation by ID.
        
        Args:
            violation_id: ID of violation
            
        Returns:
            ComplianceViolation or None
        """
        return self.db.query(ComplianceViolation).filter(
            ComplianceViolation.id == violation_id
        ).first()
    
    def update_violation(
        self,
        violation_id: int,
        update_data: ComplianceViolationUpdate,
        user_id: int,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        """
        Update a compliance violation.
        
        Args:
            violation_id: ID of violation to update
            update_data: Update data
            user_id: User making the update
            user_email: Email of user
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Updated ComplianceViolation or None
        """
        violation = self.get_violation_by_id(violation_id)
        if not violation:
            return None
        
        # Store old values for audit
        old_values = {
            "severity": violation.severity.value,
            "description": violation.description,
            "status": violation.status.value,
            "assigned_to": violation.assigned_to,
        }
        
        # Update fields
        if update_data.severity is not None:
            violation.severity = update_data.severity
        if update_data.description is not None:
            violation.description = update_data.description
        if update_data.status is not None:
            violation.status = update_data.status
        if update_data.assigned_to is not None:
            violation.assigned_to = update_data.assigned_to
        if update_data.resolution_notes is not None:
            violation.resolution_notes = update_data.resolution_notes
        if update_data.financial_impact is not None:
            violation.financial_impact = update_data.financial_impact
        if update_data.metadata is not None:
            violation.metadata = update_data.metadata
        
        # Create audit log
        last_audit = self.db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        previous_hash = last_audit.current_hash if last_audit else None
        
        audit_log = AuditLog.create_entry(
            user_id=user_id,
            user_email=user_email,
            action="UPDATE_COMPLIANCE_VIOLATION",
            resource_type="compliance_violation",
            resource_id=str(violation_id),
            old_values=old_values,
            new_values={
                "severity": violation.severity.value if update_data.severity else old_values["severity"],
                "description": violation.description if update_data.description else old_values["description"],
                "status": violation.status.value if update_data.status else old_values["status"],
                "assigned_to": violation.assigned_to if update_data.assigned_to else old_values["assigned_to"],
            },
            description=f"Updated compliance violation #{violation_id}",
            ip_address=ip_address,
            user_agent=user_agent,
            previous_hash=previous_hash
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(violation)
        
        return violation
    
    def resolve_violation(
        self,
        violation_id: int,
        resolution_notes: str,
        user_id: int,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[ComplianceViolation]:
        """
        Resolve a compliance violation.
        
        Args:
            violation_id: ID of violation
            resolution_notes: Notes about resolution
            user_id: User resolving
            user_email: Email of user
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Resolved ComplianceViolation or None
        """
        violation = self.get_violation_by_id(violation_id)
        if not violation:
            return None
        
        old_status = violation.status.value
        
        violation.status = ViolationStatus.RESOLVED
        violation.resolved_at = datetime.utcnow()
        violation.resolution_notes = resolution_notes
        
        # Create audit log
        last_audit = self.db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        previous_hash = last_audit.current_hash if last_audit else None
        
        audit_log = AuditLog.create_entry(
            user_id=user_id,
            user_email=user_email,
            action="RESOLVE_COMPLIANCE_VIOLATION",
            resource_type="compliance_violation",
            resource_id=str(violation_id),
            old_values={"status": old_status},
            new_values={"status": ViolationStatus.RESOLVED.value},
            description=f"Resolved compliance violation #{violation_id}",
            ip_address=ip_address,
            user_agent=user_agent,
            previous_hash=previous_hash
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(violation)
        
        return violation
    
    def generate_compliance_report(
        self,
        report_data: ComplianceReportCreate,
        user_id: int
    ) -> ComplianceReport:
        """
        Generate a compliance report for a time period.
        
        Args:
            report_data: Report parameters
            user_id: User generating report
            
        Returns:
            Generated ComplianceReport
        """
        # Query violations in date range
        violations = self.db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.detected_at >= datetime.combine(report_data.start_date, datetime.min.time()),
                ComplianceViolation.detected_at <= datetime.combine(report_data.end_date, datetime.max.time())
            )
        ).all()
        
        # Calculate statistics
        total_violations = len(violations)
        critical_violations = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        high_violations = sum(1 for v in violations if v.severity == ViolationSeverity.HIGH)
        medium_violations = sum(1 for v in violations if v.severity == ViolationSeverity.MEDIUM)
        low_violations = sum(1 for v in violations if v.severity == ViolationSeverity.LOW)
        
        # Build detailed report data
        report_detail = {
            "violations_by_type": {},
            "violations_by_regulation": {},
            "violations_by_status": {},
            "total_financial_impact": 0,
        }
        
        for violation in violations:
            # By type
            vtype = violation.violation_type.value
            report_detail["violations_by_type"][vtype] = report_detail["violations_by_type"].get(vtype, 0) + 1
            
            # By regulation
            reg = violation.regulation
            report_detail["violations_by_regulation"][reg] = report_detail["violations_by_regulation"].get(reg, 0) + 1
            
            # By status
            status = violation.status.value
            report_detail["violations_by_status"][status] = report_detail["violations_by_status"].get(status, 0) + 1
            
            # Financial impact
            if violation.financial_impact:
                report_detail["total_financial_impact"] += float(violation.financial_impact)
        
        # Create report
        report = ComplianceReport(
            report_type=report_data.report_type,
            start_date=report_data.start_date,
            end_date=report_data.end_date,
            total_violations=total_violations,
            critical_violations=critical_violations,
            high_violations=high_violations,
            medium_violations=medium_violations,
            low_violations=low_violations,
            generated_by=user_id,
            report_data=report_detail
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report
    
    def get_violation_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ViolationStatistics:
        """
        Get aggregated violation statistics.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            ViolationStatistics object
        """
        query = self.db.query(ComplianceViolation)
        
        if start_date:
            query = query.filter(ComplianceViolation.detected_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(ComplianceViolation.detected_at <= datetime.combine(end_date, datetime.max.time()))
        
        violations = query.all()
        
        stats = ViolationStatistics(
            total_violations=len(violations),
            open_violations=sum(1 for v in violations if v.status == ViolationStatus.OPEN),
            in_progress_violations=sum(1 for v in violations if v.status == ViolationStatus.IN_PROGRESS),
            resolved_violations=sum(1 for v in violations if v.status == ViolationStatus.RESOLVED),
            dismissed_violations=sum(1 for v in violations if v.status == ViolationStatus.DISMISSED),
            critical_violations=sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL),
            high_violations=sum(1 for v in violations if v.severity == ViolationSeverity.HIGH),
            medium_violations=sum(1 for v in violations if v.severity == ViolationSeverity.MEDIUM),
            low_violations=sum(1 for v in violations if v.severity == ViolationSeverity.LOW),
            labor_law_violations=sum(1 for v in violations if v.violation_type == ViolationType.LABOR_LAW),
            financial_violations=sum(1 for v in violations if v.violation_type == ViolationType.FINANCIAL),
            other_violations=sum(1 for v in violations if v.violation_type == ViolationType.OTHER),
            total_financial_impact=Decimal(sum(float(v.financial_impact or 0) for v in violations))
        )
        
        return stats
    
    def get_compliance_rules(
        self,
        regulation_type: Optional[RegulationType] = None,
        is_active: Optional[bool] = None
    ) -> List[ComplianceRule]:
        """
        Get compliance rules with optional filtering.
        
        Args:
            regulation_type: Optional filter by regulation type
            is_active: Optional filter by active status
            
        Returns:
            List of ComplianceRule objects
        """
        query = self.db.query(ComplianceRule)
        
        if regulation_type:
            query = query.filter(ComplianceRule.regulation_type == regulation_type)
        
        if is_active is not None:
            query = query.filter(ComplianceRule.is_active == is_active)
        
        return query.all()
