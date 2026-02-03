"""
JERP 2.0 - Federal FLSA Compliance Engine
Implements Federal Fair Labor Standards Act rules
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List


# FLSA Constants
FEDERAL_MINIMUM_WAGE = Decimal("7.25")  # Current federal minimum wage
TIPPED_MINIMUM_CASH_WAGE = Decimal("2.13")  # Minimum cash wage for tipped employees
TIPPED_CREDIT_MAX = Decimal("5.12")  # Maximum tip credit
YOUTH_MINIMUM_WAGE = Decimal("4.25")  # Youth minimum wage (first 90 days, under 20)


def calculate_flsa_overtime(hours_worked: float, regular_rate: Decimal) -> Dict[str, Any]:
    """
    Calculate overtime according to FLSA rules.
    
    FLSA Overtime:
    - 1.5x regular rate for hours over 40 in a workweek
    
    Args:
        hours_worked: Total hours worked in workweek
        regular_rate: Regular hourly rate
        
    Returns:
        Dict with regular_hours, overtime_hours, regular_pay, overtime_pay, total_pay
    """
    result = {
        "regular_hours": 0.0,
        "overtime_hours": 0.0,
        "regular_pay": Decimal("0"),
        "overtime_pay": Decimal("0"),
        "total_pay": Decimal("0"),
        "violations": []
    }
    
    hours = Decimal(str(hours_worked))
    
    if hours <= 40:
        result["regular_hours"] = float(hours)
        result["regular_pay"] = hours * regular_rate
    else:
        result["regular_hours"] = 40.0
        result["overtime_hours"] = float(hours - Decimal("40"))
        result["regular_pay"] = Decimal("40") * regular_rate
        result["overtime_pay"] = (hours - Decimal("40")) * regular_rate * Decimal("1.5")
    
    result["total_pay"] = result["regular_pay"] + result["overtime_pay"]
    
    # Convert Decimals to float for JSON serialization
    result["regular_pay"] = float(result["regular_pay"])
    result["overtime_pay"] = float(result["overtime_pay"])
    result["total_pay"] = float(result["total_pay"])
    
    return result


def validate_minimum_wage(pay: Decimal, hours: float, employee_type: str = "regular") -> Dict[str, Any]:
    """
    Validate minimum wage compliance according to FLSA.
    
    Args:
        pay: Total pay amount
        hours: Hours worked
        employee_type: Type of employee ("regular", "tipped", "youth")
        
    Returns:
        Dict with compliance status and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "effective_rate": Decimal("0"),
        "minimum_required": Decimal("0")
    }
    
    if hours == 0:
        return result
    
    effective_rate = pay / Decimal(str(hours))
    result["effective_rate"] = float(effective_rate)
    
    # Determine applicable minimum wage
    if employee_type == "tipped":
        minimum_wage = TIPPED_MINIMUM_CASH_WAGE
        result["minimum_required"] = float(minimum_wage)
        result["note"] = "Tipped employee minimum (plus tips must reach full minimum wage)"
    elif employee_type == "youth":
        minimum_wage = YOUTH_MINIMUM_WAGE
        result["minimum_required"] = float(minimum_wage)
        result["note"] = "Youth minimum wage (first 90 days, under age 20)"
    else:
        minimum_wage = FEDERAL_MINIMUM_WAGE
        result["minimum_required"] = float(minimum_wage)
    
    # Check compliance
    if effective_rate < minimum_wage:
        result["compliant"] = False
        result["violations"].append({
            "type": "MINIMUM_WAGE_VIOLATION",
            "description": f"Effective rate ${effective_rate:.2f}/hr below minimum ${minimum_wage:.2f}/hr",
            "severity": "CRITICAL",
            "standard": "FLSA_MINIMUM_WAGE",
            "shortfall": float(minimum_wage - effective_rate)
        })
    
    return result


def validate_recordkeeping(employee_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate FLSA recordkeeping requirements.
    
    Required fields per FLSA:
    - Employee name, address, SSN
    - Birth date (if under 19)
    - Sex and occupation
    - Time and day of week when workweek begins
    - Hours worked each day and total hours each workweek
    - Basis of pay (hourly, salary, etc.)
    - Regular hourly rate
    - Total daily or weekly straight-time earnings
    - Total overtime earnings
    - Additions/deductions from wages
    - Total wages paid each period
    - Date of payment and pay period
    
    Args:
        employee_record: Dict containing employee record fields
        
    Returns:
        Dict with compliance status and missing fields
    """
    result = {
        "compliant": True,
        "violations": [],
        "missing_fields": [],
        "warnings": []
    }
    
    # Required fields
    required_fields = [
        "employee_name",
        "employee_address",
        "occupation",
        "workweek_start",
        "basis_of_pay",
        "regular_rate"
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in employee_record or not employee_record[field]:
            result["missing_fields"].append(field)
            result["compliant"] = False
    
    # Check birth date for employees under 19
    if "birth_date" in employee_record:
        try:
            birth_date = datetime.strptime(employee_record["birth_date"], "%Y-%m-%d")
            age = (datetime.now() - birth_date).days / 365.25
            if age < 19 and "birth_date" not in employee_record:
                result["warnings"].append({
                    "field": "birth_date",
                    "message": "Birth date required for employees under 19"
                })
        except (ValueError, TypeError):
            pass
    
    if result["missing_fields"]:
        result["violations"].append({
            "type": "RECORDKEEPING_VIOLATION",
            "description": f"Missing required fields: {', '.join(result['missing_fields'])}",
            "severity": "HIGH",
            "standard": "FLSA_RECORDKEEPING"
        })
    
    return result


def check_child_labor_compliance(employee_age: int, hours: Dict[str, Any], occupation: str) -> Dict[str, Any]:
    """
    Check child labor compliance according to FLSA.
    
    FLSA Child Labor Rules:
    - Age 14-15: Limited hours (3 hrs/day school days, 8 hrs non-school, 18 hrs/week school weeks, 40 hrs non-school weeks)
    - Age 14-15: No hazardous occupations, limited hours (no work before 7am or after 7pm, except summer)
    - Age 16-17: No hazardous occupations
    - Age 18+: No restrictions
    
    Args:
        employee_age: Age of employee
        hours: Dict with daily_hours, weekly_hours, school_week (bool), work_start_time, work_end_time
        occupation: Job occupation/role
        
    Returns:
        Dict with compliance status and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "restrictions": []
    }
    
    # No restrictions for 18+
    if employee_age >= 18:
        result["restrictions"].append("No FLSA child labor restrictions")
        return result
    
    # Hazardous occupations list (simplified - full list in 29 CFR 570)
    hazardous_occupations = [
        "mining", "logging", "sawmill", "power-driven", "roofing",
        "excavation", "wrecking", "demolition", "manufacturing explosives",
        "motor vehicle", "coal", "forest fire", "timber", "slaughtering",
        "meat packing", "brick", "tile"
    ]
    
    # Check for hazardous occupation
    occupation_lower = occupation.lower()
    for hazard in hazardous_occupations:
        if hazard in occupation_lower:
            result["compliant"] = False
            result["violations"].append({
                "type": "HAZARDOUS_OCCUPATION",
                "description": f"Employee under 18 in hazardous occupation: {occupation}",
                "severity": "CRITICAL",
                "standard": "FLSA_CHILD_LABOR"
            })
            break
    
    # Age 16-17 restrictions
    if employee_age >= 16:
        result["restrictions"].append("No hazardous occupations")
        return result
    
    # Age 14-15 restrictions
    if employee_age >= 14:
        result["restrictions"].extend([
            "No hazardous occupations",
            "3 hours/day on school days",
            "8 hours/day on non-school days",
            "18 hours/week during school weeks",
            "40 hours/week during non-school weeks",
            "Work hours: 7am-7pm (9pm summer)"
        ])
        
        is_school_week = hours.get("school_week", True)
        daily_hours = hours.get("daily_hours", 0)
        weekly_hours = hours.get("weekly_hours", 0)
        
        # Check daily hours
        if is_school_week and daily_hours > 3:
            result["compliant"] = False
            result["violations"].append({
                "type": "EXCESSIVE_HOURS_SCHOOL_DAY",
                "description": f"Ages 14-15 limited to 3 hours on school days (worked {daily_hours})",
                "severity": "CRITICAL",
                "standard": "FLSA_CHILD_LABOR"
            })
        elif not is_school_week and daily_hours > 8:
            result["compliant"] = False
            result["violations"].append({
                "type": "EXCESSIVE_HOURS_NON_SCHOOL_DAY",
                "description": f"Ages 14-15 limited to 8 hours on non-school days (worked {daily_hours})",
                "severity": "CRITICAL",
                "standard": "FLSA_CHILD_LABOR"
            })
        
        # Check weekly hours
        if is_school_week and weekly_hours > 18:
            result["compliant"] = False
            result["violations"].append({
                "type": "EXCESSIVE_HOURS_SCHOOL_WEEK",
                "description": f"Ages 14-15 limited to 18 hours during school weeks (worked {weekly_hours})",
                "severity": "CRITICAL",
                "standard": "FLSA_CHILD_LABOR"
            })
        elif not is_school_week and weekly_hours > 40:
            result["compliant"] = False
            result["violations"].append({
                "type": "EXCESSIVE_HOURS_NON_SCHOOL_WEEK",
                "description": f"Ages 14-15 limited to 40 hours during non-school weeks (worked {weekly_hours})",
                "severity": "CRITICAL",
                "standard": "FLSA_CHILD_LABOR"
            })
        
        # Check work time restrictions
        work_start = hours.get("work_start_time")
        work_end = hours.get("work_end_time")
        
        if work_start and work_end:
            # Check if work starts before 7am or ends after 7pm (9pm in summer)
            try:
                start_hour = int(work_start.split(":")[0])
                end_hour = int(work_end.split(":")[0])
                
                if start_hour < 7:
                    result["compliant"] = False
                    result["violations"].append({
                        "type": "WORK_TIME_VIOLATION",
                        "description": "Ages 14-15 cannot work before 7am",
                        "severity": "HIGH",
                        "standard": "FLSA_CHILD_LABOR"
                    })
                
                # Simplified check - would need to check actual summer months
                max_end_hour = 19  # 7pm (would be 21/9pm in summer)
                if end_hour > max_end_hour:
                    result["compliant"] = False
                    result["violations"].append({
                        "type": "WORK_TIME_VIOLATION",
                        "description": f"Ages 14-15 cannot work after 7pm during school year (9pm summer)",
                        "severity": "HIGH",
                        "standard": "FLSA_CHILD_LABOR"
                    })
            except (ValueError, IndexError):
                pass
    else:
        # Under 14 - generally prohibited except specific exceptions (newspaper delivery, etc.)
        result["compliant"] = False
        result["violations"].append({
            "type": "AGE_VIOLATION",
            "description": "Employees under 14 generally prohibited under FLSA",
            "severity": "CRITICAL",
            "standard": "FLSA_CHILD_LABOR"
        })
    
    return result
