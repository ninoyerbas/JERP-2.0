"""
Tests for California Labor Code Compliance Engine
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.services.compliance import california_labor_code


class TestOvertimeCalculation:
    """Test California overtime calculation rules"""
    
    def test_daily_overtime_basic(self):
        """Test basic daily overtime: 1.5x for hours 8-12"""
        hours_worked = {"2024-01-01": 10}
        workweek = [datetime(2024, 1, 1)]
        
        result = california_labor_code.calculate_overtime(hours_worked, workweek)
        
        assert result["regular_hours"] == 8.0
        assert result["overtime_1_5x_hours"] == 2.0
        assert result["overtime_2x_hours"] == 0.0
    
    def test_daily_overtime_double_time(self):
        """Test daily overtime: 2x for hours beyond 12"""
        hours_worked = {"2024-01-01": 14}
        workweek = [datetime(2024, 1, 1)]
        
        result = california_labor_code.calculate_overtime(hours_worked, workweek)
        
        assert result["regular_hours"] == 8.0
        assert result["overtime_1_5x_hours"] == 4.0  # Hours 8-12
        assert result["overtime_2x_hours"] == 2.0    # Hours 12-14
    
    def test_weekly_overtime(self):
        """Test weekly overtime: 1.5x for hours over 40"""
        hours_worked = {
            "2024-01-01": 8,
            "2024-01-02": 8,
            "2024-01-03": 8,
            "2024-01-04": 8,
            "2024-01-05": 10,  # Total: 42 hours
        }
        workweek = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4),
            datetime(2024, 1, 5),
        ]
        
        result = california_labor_code.calculate_overtime(hours_worked, workweek)
        
        # 40 hours regular + 2 hours OT from weekly rule
        assert result["total_hours"] == 42.0
        assert result["regular_hours"] <= 40.0
        assert result["overtime_1_5x_hours"] >= 2.0  # At least 2 from weekly OT
    
    def test_seventh_day_overtime_basic(self):
        """Test 7th consecutive day: 1.5x for first 8 hours"""
        hours_worked = {
            "2024-01-01": 8,
            "2024-01-02": 8,
            "2024-01-03": 8,
            "2024-01-04": 8,
            "2024-01-05": 8,
            "2024-01-06": 8,
            "2024-01-07": 6,  # 7th day - all at 1.5x
        }
        workweek = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4),
            datetime(2024, 1, 5),
            datetime(2024, 1, 6),
            datetime(2024, 1, 7),
        ]
        
        result = california_labor_code.calculate_overtime(hours_worked, workweek)
        
        # 7th day hours should all be at 1.5x
        assert result["daily_breakdown"]["2024-01-07"]["ot_1_5x"] == 6.0
        assert result["daily_breakdown"]["2024-01-07"]["ot_2x"] == 0.0
        
        # Check for 7th day violation
        violations = [v for v in result["violations"] if v["type"] == "SEVENTH_DAY_WORK"]
        assert len(violations) == 1
    
    def test_seventh_day_overtime_double_time(self):
        """Test 7th consecutive day: 2x for hours beyond 8"""
        hours_worked = {
            "2024-01-01": 8,
            "2024-01-02": 8,
            "2024-01-03": 8,
            "2024-01-04": 8,
            "2024-01-05": 8,
            "2024-01-06": 8,
            "2024-01-07": 10,  # 7th day - 8 at 1.5x, 2 at 2x
        }
        workweek = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4),
            datetime(2024, 1, 5),
            datetime(2024, 1, 6),
            datetime(2024, 1, 7),
        ]
        
        result = california_labor_code.calculate_overtime(hours_worked, workweek)
        
        # 7th day: first 8 hours at 1.5x, remaining at 2x
        assert result["daily_breakdown"]["2024-01-07"]["ot_1_5x"] == 8.0
        assert result["daily_breakdown"]["2024-01-07"]["ot_2x"] == 2.0
    
    def test_consecutive_days_reset(self):
        """Test that consecutive days reset when there's a day off"""
        hours_worked = {
            "2024-01-01": 8,
            "2024-01-02": 8,
            # Day off on 01-03
            "2024-01-04": 8,
            "2024-01-05": 8,
        }
        workweek = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4),
            datetime(2024, 1, 5),
        ]
        
        result = california_labor_code.calculate_overtime(hours_worked, workweek)
        
        # Should not have 7th day violations since consecutive days reset
        violations = [v for v in result["violations"] if v["type"] == "SEVENTH_DAY_WORK"]
        assert len(violations) == 0


class TestMealBreaks:
    """Test meal break validation"""
    
    def test_meal_break_compliant(self):
        """Test compliant meal break (taken before 5th hour)"""
        shift_start = datetime(2024, 1, 1, 8, 0)   # 8 AM
        shift_end = datetime(2024, 1, 1, 17, 0)     # 5 PM (9 hours)
        
        breaks = [
            {
                "type": "meal",
                "start": datetime(2024, 1, 1, 12, 0),  # Noon
                "end": datetime(2024, 1, 1, 12, 30)     # 30 minutes
            }
        ]
        
        result = california_labor_code.validate_meal_breaks(shift_start, shift_end, breaks)
        
        assert result["compliant"] is True
        assert result["meal_breaks_taken"] == 1
        assert result["meal_breaks_required"] == 1
        assert len(result["violations"]) == 0
    
    def test_meal_break_missing(self):
        """Test violation when meal break not taken"""
        shift_start = datetime(2024, 1, 1, 8, 0)
        shift_end = datetime(2024, 1, 1, 17, 0)  # 9 hours
        
        breaks = []  # No breaks taken
        
        result = california_labor_code.validate_meal_breaks(shift_start, shift_end, breaks)
        
        assert result["compliant"] is False
        assert result["meal_breaks_required"] == 1
        assert result["meal_breaks_taken"] == 0
        
        violations = [v for v in result["violations"] if v["type"] == "MEAL_BREAK_NOT_TAKEN"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"
    
    def test_meal_break_too_short(self):
        """Test violation when meal break is too short"""
        shift_start = datetime(2024, 1, 1, 8, 0)
        shift_end = datetime(2024, 1, 1, 17, 0)
        
        breaks = [
            {
                "type": "meal",
                "start": datetime(2024, 1, 1, 12, 0),
                "end": datetime(2024, 1, 1, 12, 20)  # Only 20 minutes
            }
        ]
        
        result = california_labor_code.validate_meal_breaks(shift_start, shift_end, breaks)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "MEAL_BREAK_TOO_SHORT"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "HIGH"
    
    def test_second_meal_break_required(self):
        """Test second meal break required for shifts over 10 hours"""
        shift_start = datetime(2024, 1, 1, 8, 0)
        shift_end = datetime(2024, 1, 1, 19, 0)  # 11 hours
        
        breaks = [
            {
                "type": "meal",
                "start": datetime(2024, 1, 1, 12, 0),
                "end": datetime(2024, 1, 1, 12, 30)
            }
            # Missing second meal break
        ]
        
        result = california_labor_code.validate_meal_breaks(shift_start, shift_end, breaks)
        
        assert result["compliant"] is False
        assert result["meal_breaks_required"] == 2
        
        violations = [v for v in result["violations"] if "SECOND_MEAL_BREAK" in v["type"]]
        assert len(violations) >= 1
    
    def test_short_shift_no_meal_break_required(self):
        """Test no meal break required for shifts <= 5 hours"""
        shift_start = datetime(2024, 1, 1, 8, 0)
        shift_end = datetime(2024, 1, 1, 13, 0)  # 5 hours
        
        breaks = []
        
        result = california_labor_code.validate_meal_breaks(shift_start, shift_end, breaks)
        
        # Should be compliant - no meal break required for <= 5 hours
        assert result["meal_breaks_required"] == 0


class TestRestBreaks:
    """Test rest break validation"""
    
    def test_rest_breaks_compliant(self):
        """Test compliant rest breaks"""
        hours_worked = 8.5
        
        breaks = [
            {
                "type": "rest",
                "start": datetime(2024, 1, 1, 10, 0),
                "end": datetime(2024, 1, 1, 10, 10)  # 10 minutes
            },
            {
                "type": "rest",
                "start": datetime(2024, 1, 1, 15, 0),
                "end": datetime(2024, 1, 1, 15, 10)  # 10 minutes
            }
        ]
        
        result = california_labor_code.validate_rest_breaks(hours_worked, breaks)
        
        assert result["compliant"] is True
        assert result["rest_breaks_taken"] == 2
        assert result["rest_breaks_required"] == 2
    
    def test_rest_break_missing(self):
        """Test violation when rest breaks not taken"""
        hours_worked = 8.0
        breaks = []
        
        result = california_labor_code.validate_rest_breaks(hours_worked, breaks)
        
        assert result["compliant"] is False
        assert result["rest_breaks_required"] == 2  # 8 hours requires 2 breaks
        assert result["rest_breaks_taken"] == 0
        
        violations = [v for v in result["violations"] if v["type"] == "REST_BREAK_NOT_TAKEN"]
        assert len(violations) == 1
    
    def test_rest_break_too_short(self):
        """Test violation when rest break is too short"""
        hours_worked = 4.5
        
        breaks = [
            {
                "type": "rest",
                "start": datetime(2024, 1, 1, 10, 0),
                "end": datetime(2024, 1, 1, 10, 5)  # Only 5 minutes
            }
        ]
        
        result = california_labor_code.validate_rest_breaks(hours_worked, breaks)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "REST_BREAK_TOO_SHORT"]
        assert len(violations) == 1


class TestPenalties:
    """Test penalty calculation"""
    
    def test_meal_break_penalty(self):
        """Test penalty for meal break violation"""
        violations = [
            {
                "type": "MEAL_BREAK_NOT_TAKEN",
                "description": "Meal break not taken",
                "severity": "CRITICAL"
            }
        ]
        
        penalty = california_labor_code.calculate_penalties(violations)
        
        assert penalty == Decimal("1")  # 1 hour of pay
    
    def test_rest_break_penalty(self):
        """Test penalty for rest break violation"""
        violations = [
            {
                "type": "REST_BREAK_NOT_TAKEN",
                "description": "Rest break not taken",
                "severity": "HIGH"
            }
        ]
        
        penalty = california_labor_code.calculate_penalties(violations)
        
        assert penalty == Decimal("1")  # 1 hour of pay
    
    def test_combined_penalties(self):
        """Test combined meal and rest break penalties"""
        violations = [
            {
                "type": "MEAL_BREAK_NOT_TAKEN",
                "description": "Meal break not taken",
                "severity": "CRITICAL"
            },
            {
                "type": "REST_BREAK_NOT_TAKEN",
                "description": "Rest break not taken",
                "severity": "HIGH"
            }
        ]
        
        penalty = california_labor_code.calculate_penalties(violations)
        
        assert penalty == Decimal("2")  # 2 hours of pay (1 for each type)
    
    def test_no_penalties(self):
        """Test no penalties when compliant"""
        violations = []
        
        penalty = california_labor_code.calculate_penalties(violations)
        
        assert penalty == Decimal("0")
