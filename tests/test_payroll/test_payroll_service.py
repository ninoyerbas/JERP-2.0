"""
Tests for Payroll Service
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.payroll import PayrollPeriod, Payslip, PayrollStatus
from app.models.hr import Employee, Department, Position, EmploymentStatus, EmploymentType
from app.models.user import User
from app.models.compliance_violation import ComplianceViolation
from app.schemas.payroll import PayrollPeriodCreate, PayslipCreate, PayslipUpdate
from app.services.payroll_service import (
    create_payroll_period,
    calculate_payslip,
    create_payslip,
    update_payslip,
    process_payroll_period,
)


class TestPayrollPeriodCreation:
    """Test payroll period creation and validation"""
    
    def test_create_valid_period(self, db_session, test_user):
        """Test creating a valid payroll period"""
        period_data = PayrollPeriodCreate(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 15),
            pay_date=date(2024, 1, 20),
            notes="Test period"
        )
        
        period = create_payroll_period(period_data, test_user, db_session)
        
        assert period.id is not None
        assert period.status == PayrollStatus.DRAFT
        assert period.period_start == date(2024, 1, 1)
        assert period.period_end == date(2024, 1, 15)
        assert period.pay_date == date(2024, 1, 20)
    
    def test_invalid_date_range(self, db_session, test_user):
        """Test period end before period start raises error"""
        period_data = PayrollPeriodCreate(
            period_start=date(2024, 1, 15),
            period_end=date(2024, 1, 1),
            pay_date=date(2024, 1, 20)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            create_payroll_period(period_data, test_user, db_session)
        
        assert exc_info.value.status_code == 400
        assert "after period start" in str(exc_info.value.detail).lower()
    
    def test_overlapping_periods(self, db_session, test_user):
        """Test overlapping periods are rejected"""
        # Create first period
        period1_data = PayrollPeriodCreate(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 15),
            pay_date=date(2024, 1, 20)
        )
        create_payroll_period(period1_data, test_user, db_session)
        
        # Try to create overlapping period
        period2_data = PayrollPeriodCreate(
            period_start=date(2024, 1, 10),
            period_end=date(2024, 1, 25),
            pay_date=date(2024, 1, 30)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            create_payroll_period(period2_data, test_user, db_session)
        
        assert exc_info.value.status_code == 400
        assert "overlaps" in str(exc_info.value.detail).lower()


class TestPayslipCalculations:
    """Test payslip calculation logic"""
    
    def test_hourly_employee_regular_hours(self, db_session, test_employee_hourly, test_payroll_period):
        """Test regular hours calculation for hourly employee"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_hourly.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('0.00'),
            double_time_hours=Decimal('0.00'),
            hourly_rate=Decimal('20.00')
        )
        
        payslip = calculate_payslip(
            test_employee_hourly,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        # Regular pay should be 40 * 20 = 800
        assert payslip.regular_pay == Decimal('800.00')
        assert payslip.overtime_pay == Decimal('0.00')
        assert payslip.double_time_pay == Decimal('0.00')
        assert payslip.gross_pay >= Decimal('800.00')
    
    def test_hourly_employee_overtime(self, db_session, test_employee_hourly, test_payroll_period):
        """Test overtime calculation (FLSA 1.5x)"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_hourly.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('10.00'),
            double_time_hours=Decimal('0.00'),
            hourly_rate=Decimal('20.00')
        )
        
        payslip = calculate_payslip(
            test_employee_hourly,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        # Regular: 40 * 20 = 800
        # Overtime: 10 * 20 * 1.5 = 300
        assert payslip.regular_pay == Decimal('800.00')
        assert payslip.overtime_pay == Decimal('300.00')
        assert payslip.gross_pay >= Decimal('1100.00')
    
    def test_hourly_employee_double_time(self, db_session, test_employee_hourly, test_payroll_period):
        """Test double-time calculation (CA Labor Code 2x)"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_hourly.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('5.00'),
            double_time_hours=Decimal('3.00'),
            hourly_rate=Decimal('20.00')
        )
        
        payslip = calculate_payslip(
            test_employee_hourly,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        # Regular: 40 * 20 = 800
        # Overtime: 5 * 20 * 1.5 = 150
        # Double-time: 3 * 20 * 2.0 = 120
        assert payslip.regular_pay == Decimal('800.00')
        assert payslip.overtime_pay == Decimal('150.00')
        assert payslip.double_time_pay == Decimal('120.00')
        assert payslip.gross_pay >= Decimal('1070.00')
    
    def test_salaried_employee(self, db_session, test_employee_salaried, test_payroll_period):
        """Test salaried employee calculation (bi-weekly)"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_salaried.id,
            regular_hours=None,
            overtime_hours=None,
            double_time_hours=None,
            hourly_rate=None
        )
        
        payslip = calculate_payslip(
            test_employee_salaried,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        # Salary 60000 / 24 pay periods = 2500
        expected_pay = Decimal('60000.00') / Decimal('24')
        assert payslip.regular_pay == expected_pay
        assert payslip.overtime_pay == Decimal('0.00')
    
    def test_exempt_employee_no_overtime(self, db_session, test_employee_exempt, test_payroll_period):
        """Test exempt employee does not get overtime"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_exempt.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('10.00'),  # Should be ignored
            double_time_hours=Decimal('5.00'),  # Should be ignored
            hourly_rate=Decimal('30.00')
        )
        
        payslip = calculate_payslip(
            test_employee_exempt,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        # Exempt employees don't get overtime
        assert payslip.overtime_pay == Decimal('0.00')
        assert payslip.double_time_pay == Decimal('0.00')
    
    def test_tax_calculations(self, db_session, test_employee_hourly, test_payroll_period):
        """Test tax withholding calculations"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_hourly.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('0.00'),
            double_time_hours=Decimal('0.00'),
            hourly_rate=Decimal('20.00')
        )
        
        payslip = calculate_payslip(
            test_employee_hourly,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        gross_pay = payslip.gross_pay
        
        # Verify tax calculations (simplified rates)
        assert payslip.federal_tax == gross_pay * Decimal('0.12')
        assert payslip.state_tax == gross_pay * Decimal('0.06')
        assert payslip.social_security == gross_pay * Decimal('0.062')
        assert payslip.medicare == gross_pay * Decimal('0.0145')
    
    def test_net_pay_calculation(self, db_session, test_employee_hourly, test_payroll_period):
        """Test net pay calculation (gross - deductions)"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_hourly.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('0.00'),
            double_time_hours=Decimal('0.00'),
            hourly_rate=Decimal('20.00'),
            health_insurance=Decimal('100.00'),
            retirement_401k=Decimal('50.00')
        )
        
        payslip = calculate_payslip(
            test_employee_hourly,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        expected_net = payslip.gross_pay - payslip.total_deductions
        assert payslip.net_pay == expected_net


class TestComplianceValidation:
    """Test FLSA and CA Labor Code compliance validation"""
    
    def test_minimum_wage_violation(self, db_session, test_employee_hourly, test_payroll_period):
        """Test detection of minimum wage violation"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_hourly.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('0.00'),
            double_time_hours=Decimal('0.00'),
            hourly_rate=Decimal('10.00')  # Below CA minimum of $16
        )
        
        payslip = calculate_payslip(
            test_employee_hourly,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        # Should be flagged as non-compliant
        assert payslip.ca_labor_code_compliant == False
        assert payslip.compliance_notes is not None
        assert "minimum wage" in payslip.compliance_notes.lower()
        
        # Should create compliance violation
        db_session.flush()
        violation = db_session.query(ComplianceViolation).filter(
            ComplianceViolation.entity_type == "payslip",
            ComplianceViolation.entity_id == payslip.id
        ).first()
        
        assert violation is not None
        assert violation.severity == "CRITICAL"
    
    def test_compliant_wage(self, db_session, test_employee_hourly, test_payroll_period):
        """Test compliant wage calculation"""
        payslip_data = PayslipCreate(
            payroll_period_id=test_payroll_period.id,
            employee_id=test_employee_hourly.id,
            regular_hours=Decimal('40.00'),
            overtime_hours=Decimal('0.00'),
            double_time_hours=Decimal('0.00'),
            hourly_rate=Decimal('25.00')  # Above CA minimum
        )
        
        payslip = calculate_payslip(
            test_employee_hourly,
            test_payroll_period,
            payslip_data,
            db_session
        )
        
        # Should be compliant
        assert payslip.flsa_compliant == True
        assert payslip.ca_labor_code_compliant == True
        assert payslip.compliance_notes is None


class TestPayrollProcessing:
    """Test payroll period processing"""
    
    def test_process_payroll_period(self, db_session, test_user, test_payroll_period_with_payslips):
        """Test processing a payroll period"""
        period_id, payslips = test_payroll_period_with_payslips
        
        period = process_payroll_period(
            period_id,
            test_user,
            db_session
        )
        
        assert period.status == PayrollStatus.PROCESSED
        assert period.processed_at is not None
        assert period.processed_by == test_user.id
        assert period.total_gross > 0
        assert period.total_deductions > 0
        assert period.total_net > 0
    
    def test_process_empty_period(self, db_session, test_user, test_payroll_period):
        """Test processing period with no payslips raises error"""
        with pytest.raises(HTTPException) as exc_info:
            process_payroll_period(
                test_payroll_period.id,
                test_user,
                db_session
            )
        
        assert exc_info.value.status_code == 400
        assert "no payslips" in str(exc_info.value.detail).lower()


# Simple test that can run independently
def test_payroll_status_enum():
    """Test PayrollStatus enum values"""
    assert PayrollStatus.DRAFT == "DRAFT"
    assert PayrollStatus.PENDING == "PENDING"
    assert PayrollStatus.PROCESSING == "PROCESSING"
    assert PayrollStatus.PROCESSED == "PROCESSED"
    assert PayrollStatus.FAILED == "FAILED"
    assert PayrollStatus.CANCELLED == "CANCELLED"
