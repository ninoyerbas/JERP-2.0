"""
Tests for Federal FLSA Compliance Engine
"""
import pytest
from decimal import Decimal
from app.services.compliance import flsa


class TestFLSAOvertime:
    """Test FLSA overtime calculation"""
    
    def test_no_overtime(self):
        """Test regular hours only (no overtime)"""
        hours = 40.0
        rate = Decimal("15.00")
        
        result = flsa.calculate_flsa_overtime(hours, rate)
        
        assert result["regular_hours"] == 40.0
        assert result["overtime_hours"] == 0.0
        assert result["regular_pay"] == 600.0
        assert result["overtime_pay"] == 0.0
        assert result["total_pay"] == 600.0
    
    def test_with_overtime(self):
        """Test hours with overtime"""
        hours = 45.0
        rate = Decimal("20.00")
        
        result = flsa.calculate_flsa_overtime(hours, rate)
        
        assert result["regular_hours"] == 40.0
        assert result["overtime_hours"] == 5.0
        assert result["regular_pay"] == 800.0  # 40 * 20
        assert result["overtime_pay"] == 150.0  # 5 * 20 * 1.5
        assert result["total_pay"] == 950.0


class TestMinimumWage:
    """Test minimum wage validation"""
    
    def test_regular_employee_compliant(self):
        """Test regular employee meets minimum wage"""
        pay = Decimal("400.00")
        hours = 40.0
        
        result = flsa.validate_minimum_wage(pay, hours, "regular")
        
        assert result["compliant"] is True
        assert result["effective_rate"] == 10.0
        assert result["minimum_required"] == 7.25
    
    def test_regular_employee_violation(self):
        """Test regular employee below minimum wage"""
        pay = Decimal("250.00")
        hours = 40.0
        
        result = flsa.validate_minimum_wage(pay, hours, "regular")
        
        assert result["compliant"] is False
        assert result["effective_rate"] == 6.25
        
        violations = [v for v in result["violations"] if v["type"] == "MINIMUM_WAGE_VIOLATION"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"
    
    def test_tipped_employee(self):
        """Test tipped employee minimum cash wage"""
        pay = Decimal("100.00")
        hours = 40.0
        
        result = flsa.validate_minimum_wage(pay, hours, "tipped")
        
        assert result["minimum_required"] == 2.13
        # $100 / 40 hrs = $2.50/hr which is above tipped minimum
        assert result["compliant"] is True
    
    def test_youth_employee(self):
        """Test youth minimum wage"""
        pay = Decimal("180.00")
        hours = 40.0
        
        result = flsa.validate_minimum_wage(pay, hours, "youth")
        
        assert result["minimum_required"] == 4.25
        assert result["compliant"] is True


class TestRecordkeeping:
    """Test FLSA recordkeeping requirements"""
    
    def test_complete_record(self):
        """Test complete employee record"""
        record = {
            "employee_name": "John Doe",
            "employee_address": "123 Main St",
            "occupation": "Software Developer",
            "workweek_start": "Monday",
            "basis_of_pay": "hourly",
            "regular_rate": 25.00
        }
        
        result = flsa.validate_recordkeeping(record)
        
        assert result["compliant"] is True
        assert len(result["missing_fields"]) == 0
    
    def test_missing_fields(self):
        """Test record with missing required fields"""
        record = {
            "employee_name": "John Doe",
            "occupation": "Developer"
        }
        
        result = flsa.validate_recordkeeping(record)
        
        assert result["compliant"] is False
        assert len(result["missing_fields"]) > 0
        assert "employee_address" in result["missing_fields"]
        
        violations = [v for v in result["violations"] if v["type"] == "RECORDKEEPING_VIOLATION"]
        assert len(violations) == 1


class TestChildLabor:
    """Test child labor compliance"""
    
    def test_adult_no_restrictions(self):
        """Test no restrictions for 18+"""
        result = flsa.check_child_labor_compliance(
            employee_age=25,
            hours={"daily_hours": 10, "weekly_hours": 50},
            occupation="Manager"
        )
        
        assert result["compliant"] is True
        assert "No FLSA child labor restrictions" in result["restrictions"]
    
    def test_age_16_17_hazardous(self):
        """Test 16-17 year olds in hazardous occupation"""
        result = flsa.check_child_labor_compliance(
            employee_age=17,
            hours={"daily_hours": 8, "weekly_hours": 40},
            occupation="Mining equipment operator"
        )
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "HAZARDOUS_OCCUPATION"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"
    
    def test_age_14_15_excessive_hours_school_day(self):
        """Test 14-15 year olds exceeding school day limits"""
        result = flsa.check_child_labor_compliance(
            employee_age=15,
            hours={
                "daily_hours": 5,
                "weekly_hours": 15,
                "school_week": True
            },
            occupation="Retail clerk"
        )
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if "EXCESSIVE_HOURS" in v["type"]]
        assert len(violations) > 0
    
    def test_age_14_15_non_school_week_compliant(self):
        """Test 14-15 year olds during summer (non-school week)"""
        result = flsa.check_child_labor_compliance(
            employee_age=15,
            hours={
                "daily_hours": 8,
                "weekly_hours": 40,
                "school_week": False
            },
            occupation="Retail clerk"
        )
        
        assert result["compliant"] is True
    
    def test_age_14_15_work_time_violation(self):
        """Test 14-15 year olds working prohibited hours"""
        result = flsa.check_child_labor_compliance(
            employee_age=14,
            hours={
                "daily_hours": 3,
                "weekly_hours": 15,
                "school_week": True,
                "work_start_time": "06:00",
                "work_end_time": "15:00"
            },
            occupation="Retail clerk"
        )
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "WORK_TIME_VIOLATION"]
        assert len(violations) >= 1
    
    def test_under_14_prohibited(self):
        """Test under 14 generally prohibited"""
        result = flsa.check_child_labor_compliance(
            employee_age=13,
            hours={"daily_hours": 3, "weekly_hours": 10, "school_week": True},
            occupation="Retail clerk"
        )
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "AGE_VIOLATION"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"
