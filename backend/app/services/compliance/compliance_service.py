"""
JERP 2.0 - Compliance Service
Central service for compliance checking and violation management
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import time

from app.models.compliance import ComplianceViolation, ComplianceRule, ComplianceCheckLog
from app.models.audit_log import AuditLog
from app.services.compliance import california_labor_code, flsa, gaap, ifrs


class ComplianceService:
    """Central compliance checking service"""
    
    def check_labor_compliance(
        self, 
        employee_id: int, 
        timesheet: Dict[str, Any], 
        db: Session,
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        Run all labor law compliance checks for an employee's timesheet.
        
        Args:
            employee_id: Employee ID
            timesheet: Timesheet data with hours, breaks, etc.
            db: Database session
            user_id: ID of user performing the check
            
        Returns:
            Dict with compliance results and violations
        """
        start_time = time.time()
        
        result = {
            "employee_id": employee_id,
            "compliant": True,
            "violations": [],
            "california_labor_code": {},
            "flsa": {},
            "checks_performed": []
        }
        
        # Determine which standards apply
        state = timesheet.get("state", "CA")
        
        # California Labor Code checks
        if state == "CA":
            result["checks_performed"].append("california_labor_code")
            
            # Overtime calculation
            hours_worked = timesheet.get("hours_worked", {})
            workweek = timesheet.get("workweek", [])
            
            if hours_worked and workweek:
                ca_overtime = california_labor_code.calculate_overtime(hours_worked, workweek)
                result["california_labor_code"]["overtime"] = ca_overtime
                
                if ca_overtime.get("violations"):
                    result["violations"].extend(ca_overtime["violations"])
                    result["compliant"] = False
            
            # Meal break validation
            shift_start = timesheet.get("shift_start")
            shift_end = timesheet.get("shift_end")
            breaks = timesheet.get("breaks", [])
            
            if shift_start and shift_end:
                meal_break_result = california_labor_code.validate_meal_breaks(
                    shift_start, shift_end, breaks
                )
                result["california_labor_code"]["meal_breaks"] = meal_break_result
                
                if not meal_break_result.get("compliant"):
                    result["violations"].extend(meal_break_result["violations"])
                    result["compliant"] = False
                
                # Rest break validation
                total_hours = sum(hours_worked.values()) if hours_worked else 0
                rest_break_result = california_labor_code.validate_rest_breaks(
                    total_hours, breaks
                )
                result["california_labor_code"]["rest_breaks"] = rest_break_result
                
                if not rest_break_result.get("compliant"):
                    result["violations"].extend(rest_break_result["violations"])
                    result["compliant"] = False
                
                # Calculate penalties
                all_violations = (
                    meal_break_result.get("violations", []) +
                    rest_break_result.get("violations", [])
                )
                penalty_hours = california_labor_code.calculate_penalties(all_violations)
                result["california_labor_code"]["penalty_hours"] = float(penalty_hours)
        
        # FLSA checks (applies to all states)
        result["checks_performed"].append("flsa")
        
        total_hours = sum(timesheet.get("hours_worked", {}).values())
        regular_rate = Decimal(str(timesheet.get("regular_rate", 0)))
        
        if total_hours > 0 and regular_rate > 0:
            flsa_overtime = flsa.calculate_flsa_overtime(total_hours, regular_rate)
            result["flsa"]["overtime"] = flsa_overtime
            
            # Minimum wage check
            total_pay = Decimal(str(timesheet.get("total_pay", 0)))
            employee_type = timesheet.get("employee_type", "regular")
            
            min_wage_result = flsa.validate_minimum_wage(total_pay, total_hours, employee_type)
            result["flsa"]["minimum_wage"] = min_wage_result
            
            if not min_wage_result.get("compliant"):
                result["violations"].extend(min_wage_result["violations"])
                result["compliant"] = False
        
        # Child labor check if applicable
        employee_age = timesheet.get("employee_age")
        if employee_age and employee_age < 18:
            hours_data = {
                "daily_hours": max(timesheet.get("hours_worked", {}).values()) if timesheet.get("hours_worked") else 0,
                "weekly_hours": total_hours,
                "school_week": timesheet.get("is_school_week", True),
                "work_start_time": timesheet.get("work_start_time"),
                "work_end_time": timesheet.get("work_end_time")
            }
            occupation = timesheet.get("occupation", "")
            
            child_labor_result = flsa.check_child_labor_compliance(
                employee_age, hours_data, occupation
            )
            result["flsa"]["child_labor"] = child_labor_result
            
            if not child_labor_result.get("compliant"):
                result["violations"].extend(child_labor_result["violations"])
                result["compliant"] = False
        
        # Log compliance check
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        check_log = ComplianceCheckLog(
            check_type="LABOR_LAW",
            resource_type="timesheet",
            resource_id=str(employee_id),
            passed=result["compliant"],
            violations_found=len(result["violations"]),
            execution_time_ms=execution_time_ms,
            checked_by=user_id
        )
        db.add(check_log)
        
        # Log violations
        for violation in result["violations"]:
            self.log_violation(
                {
                    "violation_type": "LABOR_LAW",
                    "severity": violation.get("severity", "MEDIUM"),
                    "standard": violation.get("standard", "UNKNOWN"),
                    "resource_type": "timesheet",
                    "resource_id": str(employee_id),
                    "description": violation.get("description", ""),
                },
                db
            )
        
        db.commit()
        
        return result
    
    def check_financial_compliance(
        self,
        transaction: Dict[str, Any],
        standard: str,  # "GAAP" or "IFRS"
        db: Session,
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        Run financial compliance checks according to specified standard.
        
        Args:
            transaction: Transaction or financial data to check
            standard: Accounting standard ("GAAP" or "IFRS")
            db: Database session
            user_id: ID of user performing the check
            
        Returns:
            Dict with compliance results and violations
        """
        start_time = time.time()
        
        result = {
            "transaction_id": transaction.get("id", "unknown"),
            "standard": standard,
            "compliant": True,
            "violations": [],
            "checks_performed": []
        }
        
        transaction_type = transaction.get("type", "")
        
        if standard.upper() == "GAAP":
            result["checks_performed"].append("gaap")
            
            # Journal entry validation
            if transaction_type == "journal_entry":
                je_result = gaap.validate_journal_entry(transaction)
                result["journal_entry"] = je_result
                
                if not je_result.get("compliant"):
                    result["violations"].extend(je_result["violations"])
                    result["compliant"] = False
            
            # Balance sheet validation
            elif transaction_type == "balance_sheet":
                bs_result = gaap.validate_balance_sheet(
                    transaction.get("assets", {}),
                    transaction.get("liabilities", {}),
                    transaction.get("equity", {})
                )
                result["balance_sheet"] = bs_result
                
                if not bs_result.get("compliant"):
                    result["violations"].extend(bs_result["violations"])
                    result["compliant"] = False
            
            # Revenue recognition
            elif transaction_type == "revenue":
                rev_result = gaap.validate_revenue_recognition(transaction)
                result["revenue_recognition"] = rev_result
                
                if not rev_result.get("compliant"):
                    result["violations"].extend(rev_result["violations"])
                    result["compliant"] = False
            
            # Depreciation
            elif transaction_type == "depreciation":
                dep_result = gaap.validate_depreciation(
                    transaction.get("asset", {}),
                    transaction.get("method", "straight-line")
                )
                result["depreciation"] = dep_result
                
                if not dep_result.get("compliant"):
                    result["violations"].extend(dep_result["violations"])
                    result["compliant"] = False
        
        elif standard.upper() == "IFRS":
            result["checks_performed"].append("ifrs")
            
            # IFRS 15 - Revenue recognition
            if transaction_type == "revenue":
                rev_result = ifrs.validate_ifrs15_revenue(transaction)
                result["ifrs15_revenue"] = rev_result
                
                if not rev_result.get("compliant"):
                    result["violations"].extend(rev_result["violations"])
                    result["compliant"] = False
            
            # IFRS 16 - Lease
            elif transaction_type == "lease":
                lease_result = ifrs.validate_ifrs16_lease(transaction)
                result["ifrs16_lease"] = lease_result
                
                if not lease_result.get("compliant"):
                    result["violations"].extend(lease_result["violations"])
                    result["compliant"] = False
            
            # IFRS 13 - Fair value
            elif transaction_type == "fair_value":
                fv_result = ifrs.calculate_fair_value(
                    transaction.get("asset", {}),
                    transaction.get("market_data", {})
                )
                result["fair_value"] = fv_result
                
                if not fv_result.get("compliant"):
                    result["violations"].extend(fv_result["violations"])
                    result["compliant"] = False
            
            # IAS 36 - Impairment
            elif transaction_type == "impairment":
                imp_result = ifrs.validate_impairment(transaction.get("asset", {}))
                result["impairment"] = imp_result
                
                if not imp_result.get("compliant"):
                    result["violations"].extend(imp_result["violations"])
                    result["compliant"] = False
        
        # Log compliance check
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        check_log = ComplianceCheckLog(
            check_type=f"FINANCIAL_{standard.upper()}",
            resource_type=transaction_type,
            resource_id=transaction.get("id", "unknown"),
            passed=result["compliant"],
            violations_found=len(result["violations"]),
            execution_time_ms=execution_time_ms,
            checked_by=user_id
        )
        db.add(check_log)
        
        # Log violations
        for violation in result["violations"]:
            self.log_violation(
                {
                    "violation_type": "GAAP" if standard.upper() == "GAAP" else "IFRS",
                    "severity": violation.get("severity", "MEDIUM"),
                    "standard": violation.get("standard", "UNKNOWN"),
                    "resource_type": transaction_type,
                    "resource_id": transaction.get("id", "unknown"),
                    "description": violation.get("description", ""),
                },
                db
            )
        
        db.commit()
        
        return result
    
    def log_violation(
        self,
        violation: Dict[str, Any],
        db: Session
    ) -> ComplianceViolation:
        """
        Log a compliance violation with audit trail.
        
        Args:
            violation: Violation details dict
            db: Database session
            
        Returns:
            ComplianceViolation object
        """
        violation_record = ComplianceViolation(
            violation_type=violation.get("violation_type", "UNKNOWN"),
            severity=violation.get("severity", "MEDIUM"),
            standard=violation.get("standard", "UNKNOWN"),
            resource_type=violation.get("resource_type", "unknown"),
            resource_id=violation.get("resource_id", "unknown"),
            description=violation.get("description", ""),
            financial_impact=violation.get("financial_impact")
        )
        
        db.add(violation_record)
        db.flush()  # Get the ID
        
        # Create audit log entry
        audit_entry = AuditLog.create_entry(
            user_id=violation.get("user_id"),
            user_email=violation.get("user_email", "system@jerp.local"),
            action="COMPLIANCE_VIOLATION_DETECTED",
            resource_type="compliance_violation",
            resource_id=str(violation_record.id),
            new_values={
                "violation_type": violation_record.violation_type,
                "severity": violation_record.severity,
                "standard": violation_record.standard,
                "resource": f"{violation_record.resource_type}:{violation_record.resource_id}",
            },
            description=f"Compliance violation detected: {violation_record.description}",
            previous_hash=self._get_latest_audit_hash(db)
        )
        db.add(audit_entry)
        
        return violation_record
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        violation_types: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate compliance report for specified period.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            violation_types: List of violation types to include
            db: Database session
            
        Returns:
            Dict with report data
        """
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_violations": 0,
                "by_type": {},
                "by_severity": {},
                "resolved": 0,
                "unresolved": 0
            },
            "violations": [],
            "checks_performed": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        
        # Query violations
        query = db.query(ComplianceViolation).filter(
            ComplianceViolation.detected_at >= start_date,
            ComplianceViolation.detected_at <= end_date
        )
        
        if violation_types:
            query = query.filter(ComplianceViolation.violation_type.in_(violation_types))
        
        violations = query.all()
        
        # Process violations
        for violation in violations:
            report["summary"]["total_violations"] += 1
            
            # Count by type
            vtype = violation.violation_type
            report["summary"]["by_type"][vtype] = report["summary"]["by_type"].get(vtype, 0) + 1
            
            # Count by severity
            severity = violation.severity
            report["summary"]["by_severity"][severity] = report["summary"]["by_severity"].get(severity, 0) + 1
            
            # Count resolved/unresolved
            if violation.resolved_at:
                report["summary"]["resolved"] += 1
            else:
                report["summary"]["unresolved"] += 1
            
            # Add to violations list
            report["violations"].append({
                "id": violation.id,
                "type": violation.violation_type,
                "severity": violation.severity,
                "standard": violation.standard,
                "resource": f"{violation.resource_type}:{violation.resource_id}",
                "description": violation.description,
                "detected_at": violation.detected_at.isoformat(),
                "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
                "financial_impact": float(violation.financial_impact) if violation.financial_impact else None
            })
        
        # Query compliance check logs
        check_logs = db.query(ComplianceCheckLog).filter(
            ComplianceCheckLog.checked_at >= start_date,
            ComplianceCheckLog.checked_at <= end_date
        ).all()
        
        report["checks_performed"]["total"] = len(check_logs)
        report["checks_performed"]["passed"] = sum(1 for log in check_logs if log.passed)
        report["checks_performed"]["failed"] = sum(1 for log in check_logs if not log.passed)
        
        return report
    
    def _get_latest_audit_hash(self, db: Session) -> str:
        """Get the hash of the latest audit log entry."""
        latest_entry = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        return latest_entry.current_hash if latest_entry else None
