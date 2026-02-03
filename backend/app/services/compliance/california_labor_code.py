"""
JERP 2.0 - California Labor Code Compliance Engine
Implements California-specific labor law rules including overtime, meal breaks, and rest breaks
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any


def calculate_overtime(hours_worked: Dict[str, float], workweek: List[datetime]) -> Dict[str, Any]:
    """
    Calculate overtime according to California Labor Code rules.
    
    California Overtime Rules:
    - Daily: 1.5x for hours 8-12, 2x for hours >12
    - Weekly: 1.5x for hours >40 in workweek
    - 7th Day: 1.5x for first 8 hours on 7th consecutive day, 2x for hours >8 on 7th day
    
    Args:
        hours_worked: Dict mapping date (YYYY-MM-DD) to hours worked
        workweek: List of datetime objects representing the workweek dates
        
    Returns:
        Dict with regular_hours, overtime_1_5x_hours, overtime_2x_hours, and violations
    """
    result = {
        "regular_hours": Decimal("0"),
        "overtime_1_5x_hours": Decimal("0"),
        "overtime_2x_hours": Decimal("0"),
        "daily_breakdown": {},
        "violations": []
    }
    
    # Sort workweek to identify consecutive days
    sorted_dates = sorted([d.strftime("%Y-%m-%d") for d in workweek])
    total_weekly_hours = Decimal("0")
    
    # Track consecutive work days
    consecutive_days = 0
    last_date = None
    
    for date_str in sorted_dates:
        if date_str not in hours_worked:
            consecutive_days = 0
            continue
            
        hours = Decimal(str(hours_worked[date_str]))
        
        # Check for consecutive days
        if last_date:
            last = datetime.strptime(last_date, "%Y-%m-%d")
            current = datetime.strptime(date_str, "%Y-%m-%d")
            if (current - last).days == 1:
                consecutive_days += 1
            else:
                consecutive_days = 1
        else:
            consecutive_days = 1
        
        last_date = date_str
        
        daily_regular = Decimal("0")
        daily_ot_1_5x = Decimal("0")
        daily_ot_2x = Decimal("0")
        
        # 7th consecutive day special rules
        if consecutive_days >= 7:
            # 1.5x for first 8 hours on 7th day
            if hours <= 8:
                daily_ot_1_5x = hours
            else:
                # 1.5x for first 8 hours, 2x for hours beyond 8
                daily_ot_1_5x = Decimal("8")
                daily_ot_2x = hours - Decimal("8")
            
            result["violations"].append({
                "date": date_str,
                "type": "SEVENTH_DAY_WORK",
                "description": f"Employee worked {consecutive_days} consecutive days",
                "severity": "HIGH"
            })
        else:
            # Normal daily overtime rules
            if hours <= 8:
                daily_regular = hours
            elif hours <= 12:
                daily_regular = Decimal("8")
                daily_ot_1_5x = hours - Decimal("8")
            else:
                daily_regular = Decimal("8")
                daily_ot_1_5x = Decimal("4")  # Hours 8-12
                daily_ot_2x = hours - Decimal("12")
        
        result["daily_breakdown"][date_str] = {
            "regular": float(daily_regular),
            "ot_1_5x": float(daily_ot_1_5x),
            "ot_2x": float(daily_ot_2x),
            "consecutive_day": consecutive_days
        }
        
        result["regular_hours"] += daily_regular
        result["overtime_1_5x_hours"] += daily_ot_1_5x
        result["overtime_2x_hours"] += daily_ot_2x
        total_weekly_hours += hours
    
    # Apply weekly overtime rule (>40 hours)
    # Convert regular hours to overtime 1.5x if weekly total exceeds 40
    if total_weekly_hours > 40:
        excess_hours = total_weekly_hours - Decimal("40")
        if result["regular_hours"] > 0:
            hours_to_convert = min(result["regular_hours"], excess_hours)
            result["regular_hours"] -= hours_to_convert
            result["overtime_1_5x_hours"] += hours_to_convert
    
    # Convert Decimals to floats for JSON serialization
    result["regular_hours"] = float(result["regular_hours"])
    result["overtime_1_5x_hours"] = float(result["overtime_1_5x_hours"])
    result["overtime_2x_hours"] = float(result["overtime_2x_hours"])
    result["total_hours"] = float(total_weekly_hours)
    
    return result


def validate_meal_breaks(shift_start: datetime, shift_end: datetime, breaks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate meal breaks according to California Labor Code Section 512.
    
    Requirements:
    - Meal break required before end of 5th hour for shifts >5 hours
    - Meal break must be at least 30 minutes
    - Second meal break required before end of 10th hour for shifts >10 hours
    
    Args:
        shift_start: Shift start datetime
        shift_end: Shift end datetime
        breaks: List of break dicts with 'start', 'end', 'type' (type should be 'meal' or 'rest')
        
    Returns:
        Dict with compliance status and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "meal_breaks_taken": 0,
        "meal_breaks_required": 0
    }
    
    shift_duration_hours = (shift_end - shift_start).total_seconds() / 3600
    
    # Filter meal breaks
    meal_breaks = [b for b in breaks if b.get("type") == "meal"]
    result["meal_breaks_taken"] = len(meal_breaks)
    
    # Check if meal breaks are required
    if shift_duration_hours > 5:
        result["meal_breaks_required"] = 1
        
        # Check for first meal break before 5th hour
        fifth_hour_mark = shift_start + timedelta(hours=5)
        first_meal_taken = False
        
        for break_info in meal_breaks:
            break_start = break_info.get("start")
            break_end = break_info.get("end")
            
            if not break_start or not break_end:
                continue
                
            break_duration = (break_end - break_start).total_seconds() / 60  # minutes
            
            # Check if meal break is at least 30 minutes
            if break_duration < 30:
                result["violations"].append({
                    "type": "MEAL_BREAK_TOO_SHORT",
                    "description": f"Meal break only {break_duration:.1f} minutes (minimum 30 required)",
                    "severity": "HIGH",
                    "standard": "CA_LABOR_CODE_512"
                })
                result["compliant"] = False
            
            # Check if first meal break taken before 5th hour
            if break_start <= fifth_hour_mark and break_duration >= 30:
                first_meal_taken = True
        
        if not first_meal_taken:
            result["violations"].append({
                "type": "MEAL_BREAK_NOT_TAKEN",
                "description": "First meal break not taken before end of 5th hour",
                "severity": "CRITICAL",
                "standard": "CA_LABOR_CODE_512"
            })
            result["compliant"] = False
    
    # Check for second meal break if shift > 10 hours
    if shift_duration_hours > 10:
        result["meal_breaks_required"] = 2
        
        if len(meal_breaks) < 2:
            result["violations"].append({
                "type": "SECOND_MEAL_BREAK_NOT_TAKEN",
                "description": "Second meal break required for shifts over 10 hours",
                "severity": "CRITICAL",
                "standard": "CA_LABOR_CODE_512"
            })
            result["compliant"] = False
        else:
            # Check that second meal break is before 10th hour
            tenth_hour_mark = shift_start + timedelta(hours=10)
            second_meal_taken = False
            
            # Sort breaks by start time
            sorted_breaks = sorted(meal_breaks, key=lambda x: x.get("start"))
            if len(sorted_breaks) >= 2:
                second_break = sorted_breaks[1]
                if second_break.get("start") <= tenth_hour_mark:
                    second_meal_taken = True
            
            if not second_meal_taken:
                result["violations"].append({
                    "type": "SECOND_MEAL_BREAK_LATE",
                    "description": "Second meal break not taken before end of 10th hour",
                    "severity": "HIGH",
                    "standard": "CA_LABOR_CODE_512"
                })
                result["compliant"] = False
    
    return result


def validate_rest_breaks(hours_worked: float, breaks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate rest breaks according to California Labor Code.
    
    Requirements:
    - 10-minute paid rest break per 4 hours worked (or major fraction thereof)
    - Rest breaks should be in the middle of each work period
    
    Args:
        hours_worked: Total hours worked in shift
        breaks: List of break dicts with 'start', 'end', 'type'
        
    Returns:
        Dict with compliance status and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "rest_breaks_taken": 0,
        "rest_breaks_required": 0
    }
    
    # Calculate required rest breaks (one per 4 hours or major fraction)
    # Major fraction = more than 2 hours
    if hours_worked >= 3.5:
        result["rest_breaks_required"] = int((hours_worked + 2) / 4)
    
    # Filter rest breaks
    rest_breaks = [b for b in breaks if b.get("type") == "rest"]
    result["rest_breaks_taken"] = len(rest_breaks)
    
    # Check if required rest breaks were taken
    if result["rest_breaks_taken"] < result["rest_breaks_required"]:
        result["violations"].append({
            "type": "REST_BREAK_NOT_TAKEN",
            "description": f"Required {result['rest_breaks_required']} rest breaks, but only {result['rest_breaks_taken']} taken",
            "severity": "HIGH",
            "standard": "CA_LABOR_CODE_REST_BREAKS"
        })
        result["compliant"] = False
    
    # Validate rest break duration (should be at least 10 minutes)
    for break_info in rest_breaks:
        break_start = break_info.get("start")
        break_end = break_info.get("end")
        
        if break_start and break_end:
            break_duration = (break_end - break_start).total_seconds() / 60  # minutes
            
            if break_duration < 10:
                result["violations"].append({
                    "type": "REST_BREAK_TOO_SHORT",
                    "description": f"Rest break only {break_duration:.1f} minutes (minimum 10 required)",
                    "severity": "MEDIUM",
                    "standard": "CA_LABOR_CODE_REST_BREAKS"
                })
                result["compliant"] = False
    
    return result


def calculate_penalties(violations: List[Dict[str, Any]]) -> Decimal:
    """
    Calculate penalty amounts for California Labor Code violations.
    
    Penalties:
    - Meal break violation: 1 hour of pay at regular rate per day
    - Rest break violation: 1 hour of pay at regular rate per day
    
    Args:
        violations: List of violation dicts from validation functions
        
    Returns:
        Decimal penalty amount in hours of pay
    """
    penalty_hours = Decimal("0")
    
    violation_types_counted = set()
    
    for violation in violations:
        violation_type = violation.get("type", "")
        
        # Meal break violations - 1 hour penalty per day
        if "MEAL_BREAK" in violation_type and "MEAL_BREAK" not in violation_types_counted:
            penalty_hours += Decimal("1")
            violation_types_counted.add("MEAL_BREAK")
        
        # Rest break violations - 1 hour penalty per day
        if "REST_BREAK" in violation_type and "REST_BREAK" not in violation_types_counted:
            penalty_hours += Decimal("1")
            violation_types_counted.add("REST_BREAK")
    
    return penalty_hours
