"""
JERP 2.0 - Violation Tracker
Real-time violation detection and escalation management
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.compliance import ComplianceViolation, ComplianceRule


class ViolationTracker:
    """
    Manages compliance violation tracking, escalation, and resolution workflows.
    """
    
    # Severity levels in order of priority
    SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    # Auto-escalation thresholds (days)
    ESCALATION_THRESHOLDS = {
        "CRITICAL": 1,  # Escalate after 1 day
        "HIGH": 3,      # Escalate after 3 days
        "MEDIUM": 7,    # Escalate after 7 days
        "LOW": 14       # Escalate after 14 days
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_violation(
        self,
        violation: ComplianceViolation
    ) -> Dict[str, Any]:
        """
        Track a new violation and determine if escalation is needed.
        
        Args:
            violation: ComplianceViolation object
            
        Returns:
            Dict with tracking information and escalation status
        """
        result = {
            "violation_id": violation.id,
            "severity": violation.severity,
            "requires_immediate_action": False,
            "escalation_needed": False,
            "similar_violations": [],
            "recommendations": []
        }
        
        # Check for critical violations that need immediate action
        if violation.severity == "CRITICAL":
            result["requires_immediate_action"] = True
            result["recommendations"].append(
                "CRITICAL violation detected - immediate management notification required"
            )
        
        # Find similar violations
        similar = self._find_similar_violations(violation)
        result["similar_violations"] = [
            {
                "id": v.id,
                "detected_at": v.detected_at.isoformat(),
                "resolved": v.resolved_at is not None
            }
            for v in similar[:5]  # Limit to 5 most recent
        ]
        
        if len(similar) > 3:
            result["recommendations"].append(
                f"Pattern detected: {len(similar)} similar violations found. "
                "Consider root cause analysis."
            )
        
        return result
    
    def check_escalations(self) -> List[Dict[str, Any]]:
        """
        Check for violations that need escalation based on age and severity.
        
        Returns:
            List of violations needing escalation
        """
        escalations = []
        
        # Query unresolved violations
        unresolved = self.db.query(ComplianceViolation).filter(
            ComplianceViolation.resolved_at.is_(None)
        ).all()
        
        now = datetime.utcnow()
        
        for violation in unresolved:
            age_days = (now - violation.detected_at).days
            threshold = self.ESCALATION_THRESHOLDS.get(violation.severity, 30)
            
            if age_days >= threshold:
                escalations.append({
                    "violation_id": violation.id,
                    "severity": violation.severity,
                    "age_days": age_days,
                    "threshold_days": threshold,
                    "standard": violation.standard,
                    "resource": f"{violation.resource_type}:{violation.resource_id}",
                    "description": violation.description,
                    "escalation_reason": f"Unresolved for {age_days} days (threshold: {threshold} days)"
                })
        
        return escalations
    
    def resolve_violation(
        self,
        violation_id: int,
        resolution_notes: str,
        resolved_by: int = None
    ) -> Dict[str, Any]:
        """
        Mark a violation as resolved.
        
        Args:
            violation_id: Violation ID
            resolution_notes: Notes about resolution
            resolved_by: User ID who resolved it
            
        Returns:
            Dict with resolution status
        """
        violation = self.db.query(ComplianceViolation).filter(
            ComplianceViolation.id == violation_id
        ).first()
        
        if not violation:
            return {
                "success": False,
                "error": "Violation not found"
            }
        
        if violation.resolved_at:
            return {
                "success": False,
                "error": "Violation already resolved",
                "resolved_at": violation.resolved_at.isoformat()
            }
        
        violation.resolved_at = datetime.utcnow()
        violation.resolution_notes = resolution_notes
        
        self.db.commit()
        
        # Calculate resolution time
        resolution_time_hours = (violation.resolved_at - violation.detected_at).total_seconds() / 3600
        
        return {
            "success": True,
            "violation_id": violation_id,
            "resolved_at": violation.resolved_at.isoformat(),
            "resolution_time_hours": round(resolution_time_hours, 2)
        }
    
    def get_violation_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics on violations for specified period.
        
        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            Dict with violation analytics
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        analytics = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total": 0,
                "resolved": 0,
                "unresolved": 0,
                "avg_resolution_time_hours": 0
            },
            "by_type": {},
            "by_severity": {},
            "by_standard": {},
            "trends": [],
            "top_resources": []
        }
        
        # Query violations in period
        violations = self.db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.detected_at >= start_date,
                ComplianceViolation.detected_at <= end_date
            )
        ).all()
        
        analytics["summary"]["total"] = len(violations)
        
        resolution_times = []
        type_counts = {}
        severity_counts = {}
        standard_counts = {}
        resource_counts = {}
        
        for violation in violations:
            # Count resolved/unresolved
            if violation.resolved_at:
                analytics["summary"]["resolved"] += 1
                
                # Calculate resolution time
                resolution_time = (violation.resolved_at - violation.detected_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
            else:
                analytics["summary"]["unresolved"] += 1
            
            # Count by type
            vtype = violation.violation_type
            type_counts[vtype] = type_counts.get(vtype, 0) + 1
            
            # Count by severity
            severity = violation.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by standard
            standard = violation.standard
            standard_counts[standard] = standard_counts.get(standard, 0) + 1
            
            # Count by resource
            resource_key = f"{violation.resource_type}:{violation.resource_id}"
            resource_counts[resource_key] = resource_counts.get(resource_key, 0) + 1
        
        # Calculate average resolution time
        if resolution_times:
            analytics["summary"]["avg_resolution_time_hours"] = round(
                sum(resolution_times) / len(resolution_times), 2
            )
        
        # Populate breakdowns
        analytics["by_type"] = type_counts
        analytics["by_severity"] = severity_counts
        analytics["by_standard"] = standard_counts
        
        # Top resources with most violations
        sorted_resources = sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)
        analytics["top_resources"] = [
            {"resource": k, "count": v}
            for k, v in sorted_resources[:10]
        ]
        
        # Calculate daily trends
        date_counts = {}
        for violation in violations:
            date_key = violation.detected_at.date().isoformat()
            date_counts[date_key] = date_counts.get(date_key, 0) + 1
        
        analytics["trends"] = [
            {"date": date, "count": count}
            for date, count in sorted(date_counts.items())
        ]
        
        return analytics
    
    def get_violations_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        include_resolved: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all violations for a specific resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            include_resolved: Include resolved violations
            
        Returns:
            List of violations
        """
        query = self.db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.resource_type == resource_type,
                ComplianceViolation.resource_id == resource_id
            )
        )
        
        if not include_resolved:
            query = query.filter(ComplianceViolation.resolved_at.is_(None))
        
        violations = query.order_by(ComplianceViolation.detected_at.desc()).all()
        
        return [
            {
                "id": v.id,
                "type": v.violation_type,
                "severity": v.severity,
                "standard": v.standard,
                "description": v.description,
                "detected_at": v.detected_at.isoformat(),
                "resolved_at": v.resolved_at.isoformat() if v.resolved_at else None,
                "financial_impact": float(v.financial_impact) if v.financial_impact else None
            }
            for v in violations
        ]
    
    def classify_severity(
        self,
        violation_type: str,
        standard: str,
        financial_impact: Optional[float] = None
    ) -> str:
        """
        Classify violation severity based on type, standard, and impact.
        
        Args:
            violation_type: Type of violation
            standard: Compliance standard
            financial_impact: Financial impact in dollars
            
        Returns:
            Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        """
        # Critical violations
        critical_standards = [
            "CA_LABOR_CODE_512",  # Meal breaks
            "FLSA_MINIMUM_WAGE",  # Minimum wage
            "FLSA_CHILD_LABOR",   # Child labor
            "GAAP_FUNDAMENTAL_EQUATION",  # Balance sheet
            "IFRS_15_IDENTIFICATION"  # Contract identification
        ]
        
        if any(std in standard for std in critical_standards):
            return "CRITICAL"
        
        # High violations based on financial impact
        if financial_impact:
            if financial_impact > 10000:
                return "CRITICAL"
            elif financial_impact > 1000:
                return "HIGH"
            elif financial_impact > 100:
                return "MEDIUM"
        
        # High violations based on type
        if "CHILD_LABOR" in standard or "MINIMUM_WAGE" in standard:
            return "CRITICAL"
        
        if "OVERTIME" in standard or "MEAL_BREAK" in standard or "REST_BREAK" in standard:
            return "HIGH"
        
        # Medium violations
        if violation_type in ["GAAP", "IFRS"]:
            if "IMPAIRMENT" in standard or "DEPRECIATION" in standard:
                return "MEDIUM"
        
        # Default to MEDIUM
        return "MEDIUM"
    
    def _find_similar_violations(
        self,
        violation: ComplianceViolation,
        days_back: int = 30
    ) -> List[ComplianceViolation]:
        """
        Find similar violations in recent history.
        
        Args:
            violation: Violation to find similar ones for
            days_back: How many days to look back
            
        Returns:
            List of similar violations
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        similar = self.db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.id != violation.id,
                ComplianceViolation.violation_type == violation.violation_type,
                ComplianceViolation.standard == violation.standard,
                ComplianceViolation.detected_at >= cutoff_date
            )
        ).order_by(ComplianceViolation.detected_at.desc()).all()
        
        return similar
