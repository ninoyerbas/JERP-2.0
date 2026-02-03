"""
JERP 2.0 - Payroll Models
Payroll processing with automatic compliance checking
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.core.database import Base


class PayrollPeriod(Base):
    """Payroll processing periods"""
    __tablename__ = "payroll_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)
    status = Column(String(20))  # DRAFT, PROCESSING, APPROVED, PAID
    processed_by = Column(Integer, ForeignKey("users.id"))
    processed_at = Column(DateTime)
    total_gross = Column(DECIMAL(15, 2))
    total_deductions = Column(DECIMAL(15, 2))
    total_net = Column(DECIMAL(15, 2))
    compliance_checked = Column(Boolean, default=False)
    compliance_violations_count = Column(Integer, default=0)
    
    processor = relationship("User")
    payslips = relationship("Payslip", back_populates="period")


class Payslip(Base):
    """Individual employee payslips with compliance validation"""
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Earnings
    regular_hours = Column(DECIMAL(10, 2), default=0)
    overtime_hours = Column(DECIMAL(10, 2), default=0)
    double_time_hours = Column(DECIMAL(10, 2), default=0)
    regular_pay = Column(DECIMAL(15, 2), default=0)
    overtime_pay = Column(DECIMAL(15, 2), default=0)
    double_time_pay = Column(DECIMAL(15, 2), default=0)
    bonus = Column(DECIMAL(15, 2), default=0)
    commission = Column(DECIMAL(15, 2), default=0)
    
    # California Labor Code Penalties
    meal_break_penalty = Column(DECIMAL(15, 2), default=0)
    rest_break_penalty = Column(DECIMAL(15, 2), default=0)
    
    # Deductions
    federal_tax = Column(DECIMAL(15, 2), default=0)
    state_tax = Column(DECIMAL(15, 2), default=0)
    social_security = Column(DECIMAL(15, 2), default=0)
    medicare = Column(DECIMAL(15, 2), default=0)
    
    # Totals
    gross_pay = Column(DECIMAL(15, 2), nullable=False)
    total_deductions = Column(DECIMAL(15, 2), nullable=False)
    net_pay = Column(DECIMAL(15, 2), nullable=False)
    
    # Compliance Tracking
    california_labor_compliant = Column(Boolean, default=True)
    flsa_compliant = Column(Boolean, default=True)
    compliance_notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    period = relationship("PayrollPeriod", back_populates="payslips")
    employee = relationship("Employee")
    approver = relationship("User", foreign_keys=[approved_by])
