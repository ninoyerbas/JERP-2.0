"""
JERP 2.0 - Federal Fair Labor Standards Act (FLSA) Compliance Engine
Implements federal labor law requirements for overtime, minimum wage, and employee classification
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class EmployeeClassification(str, Enum):
    """FLSA employee classification types"""
    EXEMPT = "EXEMPT"
    NON_EXEMPT = "NON_EXEMPT"


class ExemptionType(str, Enum):
    """Types of FLSA exemptions"""
    EXECUTIVE = "EXECUTIVE"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    PROFESSIONAL = "PROFESSIONAL"
    COMPUTER = "COMPUTER"
    OUTSIDE_SALES = "OUTSIDE_SALES"
    HIGHLY_COMPENSATED = "HIGHLY_COMPENSATED"
    NONE = "NONE"


@dataclass
class FLSAOvertimeCalculation:
    """Result of FLSA overtime calculation"""
    regular_hours: Decimal
    overtime_hours: Decimal
    regular_pay: Decimal
    overtime_pay: Decimal
    total_pay: Decimal


@dataclass
class ChildLaborViolation:
    """Represents a child labor law violation"""
    date: date
    employee_age: int
    hours_worked: Decimal
    violation_description: str
    severity: str


class FLSA:
    """
    Federal Fair Labor Standards Act (FLSA) compliance engine.
    
    Key regulations implemented:
    - Section 7: Overtime pay (1.5x for hours over 40 per week)
    - Section 6: Minimum wage
    - Section 13: Employee exemptions
    - Section 12: Child labor restrictions
    - Section 11: Record keeping requirements
    """
    
    # Constants
    WEEKLY_OVERTIME_THRESHOLD = Decimal("40.0")
    OVERTIME_RATE = Decimal("1.5")
    
    # Federal minimum wage (current as of 2024)
    FEDERAL_MINIMUM_WAGE = Decimal("7.25")
    
    # Exemption thresholds (as of 2024)
    EXEMPT_SALARY_THRESHOLD = Decimal("684.00")  # per week
    HIGHLY_COMPENSATED_THRESHOLD = Decimal("107432.00")  # per year
    
    # Child labor age thresholds
    MINIMUM_WORK_AGE = 14
    HAZARDOUS_WORK_AGE = 18
    UNRESTRICTED_WORK_AGE = 18
    
    # Child labor hour restrictions (ages 14-15)
    CHILD_MAX_HOURS_SCHOOL_DAY = Decimal("3.0")
    CHILD_MAX_HOURS_NON_SCHOOL_DAY = Decimal("8.0")
    CHILD_MAX_HOURS_SCHOOL_WEEK = Decimal("18.0")
    CHILD_MAX_HOURS_NON_SCHOOL_WEEK = Decimal("40.0")
    
    def __init__(self):
        """Initialize FLSA compliance engine"""
        pass
    
    def calculate_weekly_overtime(
        self,
        hours_worked: Decimal,
        regular_rate: Decimal
    ) -> FLSAOvertimeCalculation:
        """
        Calculate FLSA weekly overtime.
        
        FLSA Rule: 1.5x pay for hours over 40 in a workweek
        
        Args:
            hours_worked: Total hours worked in the week
            regular_rate: Employee's regular hourly rate
            
        Returns:
            FLSAOvertimeCalculation with breakdown
        """
        if hours_worked <= self.WEEKLY_OVERTIME_THRESHOLD:
            regular_hours = hours_worked
            overtime_hours = Decimal("0")
        else:
            regular_hours = self.WEEKLY_OVERTIME_THRESHOLD
            overtime_hours = hours_worked - self.WEEKLY_OVERTIME_THRESHOLD
        
        regular_pay = regular_hours * regular_rate
        overtime_pay = overtime_hours * regular_rate * self.OVERTIME_RATE
        total_pay = regular_pay + overtime_pay
        
        return FLSAOvertimeCalculation(
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            regular_pay=regular_pay,
            overtime_pay=overtime_pay,
            total_pay=total_pay
        )
    
    def validate_minimum_wage(
        self,
        hourly_rate: Decimal,
        state_minimum_wage: Optional[Decimal] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that hourly rate meets federal (and optionally state) minimum wage.
        
        Args:
            hourly_rate: Employee's hourly rate
            state_minimum_wage: Optional state minimum wage (use higher of state/federal)
            
        Returns:
            Tuple of (is_valid, violation_message)
        """
        applicable_minimum = self.FEDERAL_MINIMUM_WAGE
        minimum_source = "federal"
        
        if state_minimum_wage and state_minimum_wage > self.FEDERAL_MINIMUM_WAGE:
            applicable_minimum = state_minimum_wage
            minimum_source = "state"
        
        if hourly_rate < applicable_minimum:
            return False, f"Hourly rate ${hourly_rate} is below {minimum_source} minimum wage of ${applicable_minimum}"
        return True, None
    
    def check_exempt_classification(
        self,
        job_title: str,
        weekly_salary: Decimal,
        annual_salary: Optional[Decimal],
        job_duties: List[str],
        exemption_type: ExemptionType
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if employee qualifies for exempt status under FLSA.
        
        Requirements for exemption:
        1. Salary basis test: Paid fixed salary (not hourly)
        2. Salary level test: Minimum weekly salary threshold
        3. Duties test: Job duties meet exemption criteria
        
        Args:
            job_title: Employee's job title
            weekly_salary: Weekly salary amount
            annual_salary: Annual salary (for highly compensated check)
            job_duties: List of primary job duties
            exemption_type: Type of exemption being claimed
            
        Returns:
            Tuple of (is_exempt, reason_if_not_exempt)
        """
        # Check salary level test
        if exemption_type != ExemptionType.HIGHLY_COMPENSATED:
            if weekly_salary < self.EXEMPT_SALARY_THRESHOLD:
                return False, f"Weekly salary ${weekly_salary} is below minimum threshold of ${self.EXEMPT_SALARY_THRESHOLD}"
        
        # Check highly compensated exemption
        if exemption_type == ExemptionType.HIGHLY_COMPENSATED:
            if not annual_salary or annual_salary < self.HIGHLY_COMPENSATED_THRESHOLD:
                return False, f"Annual salary does not meet highly compensated threshold of ${self.HIGHLY_COMPENSATED_THRESHOLD}"
        
        # Duties test (simplified - in real implementation, would need more detailed checks)
        required_duties = self._get_required_duties_for_exemption(exemption_type)
        if not required_duties:
            return False, f"Unknown exemption type: {exemption_type}"
        
        # Check if job duties align with exemption type
        # (This is a simplified check - real implementation would be more thorough)
        duties_match = any(duty.lower() in ' '.join(job_duties).lower() for duty in required_duties)
        
        if not duties_match:
            return False, f"Job duties do not meet requirements for {exemption_type} exemption"
        
        return True, None
    
    def _get_required_duties_for_exemption(self, exemption_type: ExemptionType) -> List[str]:
        """Get required duty keywords for exemption type"""
        duties_map = {
            ExemptionType.EXECUTIVE: ["manage", "supervise", "director", "manager"],
            ExemptionType.ADMINISTRATIVE: ["administrative", "policy", "business operations"],
            ExemptionType.PROFESSIONAL: ["advanced knowledge", "professional", "licensed"],
            ExemptionType.COMPUTER: ["computer", "programmer", "systems", "software"],
            ExemptionType.OUTSIDE_SALES: ["sales", "outside", "client", "revenue"],
            ExemptionType.HIGHLY_COMPENSATED: [],  # No specific duties required
        }
        return duties_map.get(exemption_type, [])
    
    def check_child_labor_compliance(
        self,
        employee_age: int,
        hours_worked: Decimal,
        work_date: date,
        is_school_day: bool,
        is_school_week: bool,
        is_hazardous_work: bool = False
    ) -> List[ChildLaborViolation]:
        """
        Check compliance with FLSA child labor laws.
        
        Rules:
        - Minimum age 14 for non-agricultural work
        - Ages 14-15: Limited hours and no hazardous work
        - Ages 16-17: No hour restrictions but no hazardous work
        - Age 18+: No restrictions
        
        Args:
            employee_age: Employee's age in years
            hours_worked: Hours worked on the given day/week
            work_date: Date of work
            is_school_day: Whether this is a school day
            is_school_week: Whether this is a school week
            is_hazardous_work: Whether the work is classified as hazardous
            
        Returns:
            List of ChildLaborViolation objects
        """
        violations = []
        
        # Age restrictions
        if employee_age < self.MINIMUM_WORK_AGE:
            violations.append(ChildLaborViolation(
                date=work_date,
                employee_age=employee_age,
                hours_worked=hours_worked,
                violation_description=f"Employee under minimum work age of {self.MINIMUM_WORK_AGE}",
                severity="CRITICAL"
            ))
            return violations  # No need to check further
        
        # Hazardous work restrictions
        if is_hazardous_work and employee_age < self.HAZARDOUS_WORK_AGE:
            violations.append(ChildLaborViolation(
                date=work_date,
                employee_age=employee_age,
                hours_worked=hours_worked,
                violation_description=f"Employee under {self.HAZARDOUS_WORK_AGE} performing hazardous work",
                severity="CRITICAL"
            ))
        
        # Hour restrictions for ages 14-15
        if employee_age >= 14 and employee_age < 16:
            if is_school_day:
                if hours_worked > self.CHILD_MAX_HOURS_SCHOOL_DAY:
                    violations.append(ChildLaborViolation(
                        date=work_date,
                        employee_age=employee_age,
                        hours_worked=hours_worked,
                        violation_description=f"Exceeded maximum hours ({self.CHILD_MAX_HOURS_SCHOOL_DAY}) for school day",
                        severity="HIGH"
                    ))
            else:
                if hours_worked > self.CHILD_MAX_HOURS_NON_SCHOOL_DAY:
                    violations.append(ChildLaborViolation(
                        date=work_date,
                        employee_age=employee_age,
                        hours_worked=hours_worked,
                        violation_description=f"Exceeded maximum hours ({self.CHILD_MAX_HOURS_NON_SCHOOL_DAY}) for non-school day",
                        severity="HIGH"
                    ))
            
            if is_school_week:
                if hours_worked > self.CHILD_MAX_HOURS_SCHOOL_WEEK:
                    violations.append(ChildLaborViolation(
                        date=work_date,
                        employee_age=employee_age,
                        hours_worked=hours_worked,
                        violation_description=f"Exceeded maximum hours ({self.CHILD_MAX_HOURS_SCHOOL_WEEK}) for school week",
                        severity="HIGH"
                    ))
            else:
                if hours_worked > self.CHILD_MAX_HOURS_NON_SCHOOL_WEEK:
                    violations.append(ChildLaborViolation(
                        date=work_date,
                        employee_age=employee_age,
                        hours_worked=hours_worked,
                        violation_description=f"Exceeded maximum hours ({self.CHILD_MAX_HOURS_NON_SCHOOL_WEEK}) for non-school week",
                        severity="HIGH"
                    ))
        
        return violations
    
    def check_record_keeping_requirements(
        self,
        employee_id: int,
        has_name: bool,
        has_address: bool,
        has_ssn: bool,
        has_birth_date: bool,
        has_occupation: bool,
        has_hourly_rate: bool,
        has_hours_worked_records: bool,
        has_wages_paid_records: bool
    ) -> List[str]:
        """
        Check FLSA record keeping requirements.
        
        Employers must maintain records including:
        - Employee identifying information
        - Hours worked each day and week
        - Wages paid
        - Deductions
        
        Args:
            Various boolean flags indicating presence of required records
            
        Returns:
            List of missing record types
        """
        missing_records = []
        
        if not has_name:
            missing_records.append("Employee full name")
        if not has_address:
            missing_records.append("Employee home address")
        if not has_ssn:
            missing_records.append("Employee Social Security Number")
        if not has_birth_date:
            missing_records.append("Employee birth date (if under 19)")
        if not has_occupation:
            missing_records.append("Employee occupation")
        if not has_hourly_rate:
            missing_records.append("Hourly rate of pay")
        if not has_hours_worked_records:
            missing_records.append("Hours worked each workday and workweek")
        if not has_wages_paid_records:
            missing_records.append("Total wages paid each pay period")
        
        return missing_records
    
    def calculate_compensatory_time(
        self,
        overtime_hours: Decimal,
        is_public_sector: bool = False
    ) -> Tuple[Decimal, Optional[str]]:
        """
        Calculate compensatory time off (comp time) for public sector employees.
        
        FLSA allows public sector employers to provide comp time instead of overtime pay.
        Rate: 1.5 hours of comp time for each overtime hour worked.
        
        Args:
            overtime_hours: Hours of overtime worked
            is_public_sector: Whether employer is public sector
            
        Returns:
            Tuple of (comp_time_hours, error_message)
        """
        if not is_public_sector:
            return Decimal("0"), "Compensatory time is only allowed for public sector employees"
        
        comp_time_hours = overtime_hours * Decimal("1.5")
        return comp_time_hours, None
    
    def validate_salary_basis(
        self,
        pay_type: str,
        guaranteed_weekly_amount: Optional[Decimal]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that employee is paid on a salary basis (for exempt classification).
        
        Salary basis means:
        - Regular predetermined amount
        - Not subject to reduction based on quality/quantity of work
        - Full salary for any week work is performed
        
        Args:
            pay_type: "salary", "hourly", or "commission"
            guaranteed_weekly_amount: Guaranteed weekly pay amount
            
        Returns:
            Tuple of (is_salary_basis, violation_message)
        """
        if pay_type.lower() not in ["salary", "salaried"]:
            return False, f"Pay type '{pay_type}' does not meet salary basis requirement"
        
        if not guaranteed_weekly_amount or guaranteed_weekly_amount < self.EXEMPT_SALARY_THRESHOLD:
            return False, f"Guaranteed weekly amount does not meet minimum threshold"
        
        return True, None
