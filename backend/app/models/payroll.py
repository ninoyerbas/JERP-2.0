"""
JERP 2.0 - Payroll Models
Payroll period and payslip models with FLSA/CA Labor Code compliance tracking
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Numeric, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class PayrollStatus(str, enum.Enum):
    """Payroll period status enumeration"""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PayrollPeriod(Base):
    """Payroll period model for managing pay periods"""
    __tablename__ = "payroll_periods"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Period dates
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    pay_date = Column(Date, nullable=False)
    
    # Status
    status = Column(SQLEnum(PayrollStatus), default=PayrollStatus.DRAFT, nullable=False, index=True)
    
    # Totals
    total_gross = Column(Numeric(12, 2), nullable=True)
    total_deductions = Column(Numeric(12, 2), nullable=True)
    total_net = Column(Numeric(12, 2), nullable=True)
    
    # Processing information
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_by_user = relationship("User", foreign_keys=[processed_by])
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    payslips = relationship("Payslip", back_populates="payroll_period")

    def __repr__(self):
        return f"<PayrollPeriod(id={self.id}, period={self.period_start} to {self.period_end}, status='{self.status}')>"

    __table_args__ = (
        Index('idx_payroll_period_dates', 'period_start', 'period_end'),
        Index('idx_payroll_period_status', 'status'),
    )


class Payslip(Base):
    """Payslip model with comprehensive pay calculations and compliance tracking"""
    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # References
    payroll_period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    
    # Hours and rates
    regular_hours = Column(Numeric(8, 2), nullable=True)
    overtime_hours = Column(Numeric(8, 2), nullable=True)
    double_time_hours = Column(Numeric(8, 2), nullable=True)
    hourly_rate = Column(Numeric(8, 2), nullable=True)
    
    # Gross pay components
    regular_pay = Column(Numeric(12, 2), nullable=False, default=0)
    overtime_pay = Column(Numeric(12, 2), nullable=False, default=0)
    double_time_pay = Column(Numeric(12, 2), nullable=False, default=0)
    bonus = Column(Numeric(12, 2), nullable=False, default=0)
    commission = Column(Numeric(12, 2), nullable=False, default=0)
    other_earnings = Column(Numeric(12, 2), nullable=False, default=0)
    gross_pay = Column(Numeric(12, 2), nullable=False)
    
    # Deductions
    federal_tax = Column(Numeric(12, 2), nullable=False, default=0)
    state_tax = Column(Numeric(12, 2), nullable=False, default=0)
    social_security = Column(Numeric(12, 2), nullable=False, default=0)
    medicare = Column(Numeric(12, 2), nullable=False, default=0)
    health_insurance = Column(Numeric(12, 2), nullable=False, default=0)
    retirement_401k = Column(Numeric(12, 2), nullable=False, default=0)
    other_deductions = Column(Numeric(12, 2), nullable=False, default=0)
    total_deductions = Column(Numeric(12, 2), nullable=False)
    
    # Net pay
    net_pay = Column(Numeric(12, 2), nullable=False)
    
    # Compliance flags
    flsa_compliant = Column(Boolean, default=True, nullable=False)
    ca_labor_code_compliant = Column(Boolean, default=True, nullable=False)
    compliance_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    payroll_period = relationship("PayrollPeriod", back_populates="payslips")
    employee = relationship("Employee")

    def __repr__(self):
        return f"<Payslip(id={self.id}, employee_id={self.employee_id}, gross_pay={self.gross_pay})>"

    __table_args__ = (
        Index('idx_payslip_employee_period', 'employee_id', 'payroll_period_id'),
        Index('idx_payslip_compliance', 'flsa_compliant', 'ca_labor_code_compliant'),
    )
