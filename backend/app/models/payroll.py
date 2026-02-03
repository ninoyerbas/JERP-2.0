"""
JERP 2.0 - Payroll Models
Payroll period and payslip models with FLSA/CA Labor Code compliance tracking
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Numeric, Text, Enum as SQLEnum, Index
Pay periods, payslips, and payroll management models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric, Text, Enum as SQLEnum, Index
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
class PayPeriodStatus(str, enum.Enum):
    """Pay period status enumeration"""
    OPEN = "OPEN"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CLOSED = "CLOSED"


class PayPeriodType(str, enum.Enum):
    """Pay period type enumeration"""
    WEEKLY = "WEEKLY"
    BI_WEEKLY = "BI_WEEKLY"
    SEMI_MONTHLY = "SEMI_MONTHLY"
    MONTHLY = "MONTHLY"


class PayPeriod(Base):
    """Pay period model for managing payroll cycles"""
    __tablename__ = "pay_periods"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    pay_date = Column(Date, nullable=False, index=True)
    period_type = Column(SQLEnum(PayPeriodType), nullable=False)
    status = Column(SQLEnum(PayPeriodStatus), default=PayPeriodStatus.OPEN, nullable=False, index=True)
    
    # Approval workflow
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
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
    payslips = relationship("Payslip", back_populates="pay_period", cascade="all, delete-orphan")
    processed_by_user = relationship("User", foreign_keys=[processed_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<PayPeriod(id={self.id}, period={self.start_date} to {self.end_date}, status='{self.status}')>"
    
    __table_args__ = (
        Index('idx_pay_period_dates', 'start_date', 'end_date'),
        Index('idx_pay_period_status', 'status', 'pay_date'),
    )


class PayslipStatus(str, enum.Enum):
    """Payslip status enumeration"""
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    APPROVED = "APPROVED"
    PAID = "PAID"
    VOIDED = "VOIDED"


class Payslip(Base):
    """Payslip model for individual employee pay records"""
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Relationships
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    employee = relationship("Employee")
    
    pay_period_id = Column(Integer, ForeignKey("pay_periods.id"), nullable=False, index=True)
    pay_period = relationship("PayPeriod", back_populates="payslips")
    
    # Status
    status = Column(SQLEnum(PayslipStatus), default=PayslipStatus.DRAFT, nullable=False, index=True)
    
    # Earnings
    regular_hours = Column(Numeric(8, 2), default=0, nullable=False)
    overtime_hours = Column(Numeric(8, 2), default=0, nullable=False)
    regular_pay = Column(Numeric(12, 2), default=0, nullable=False)
    overtime_pay = Column(Numeric(12, 2), default=0, nullable=False)
    bonus = Column(Numeric(12, 2), default=0, nullable=False)
    commission = Column(Numeric(12, 2), default=0, nullable=False)
    gross_pay = Column(Numeric(12, 2), nullable=False)
    
    # Deductions
    federal_tax = Column(Numeric(12, 2), default=0, nullable=False)
    state_tax = Column(Numeric(12, 2), default=0, nullable=False)
    social_security = Column(Numeric(12, 2), default=0, nullable=False)
    medicare = Column(Numeric(12, 2), default=0, nullable=False)
    health_insurance = Column(Numeric(12, 2), default=0, nullable=False)
    retirement_401k = Column(Numeric(12, 2), default=0, nullable=False)
    other_deductions = Column(Numeric(12, 2), default=0, nullable=False)
    total_deductions = Column(Numeric(12, 2), nullable=False)
    
    # Net pay
    net_pay = Column(Numeric(12, 2), nullable=False)
    
    # Compliance flags
    flsa_compliant = Column(Boolean, default=True, nullable=False)
    ca_labor_code_compliant = Column(Boolean, default=True, nullable=False)
    compliance_notes = Column(Text, nullable=True)
    # Payment details
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
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
    def __repr__(self):
        return f"<Payslip(id={self.id}, employee_id={self.employee_id}, status='{self.status}', net_pay={self.net_pay})>"
    
    __table_args__ = (
        Index('idx_payslip_employee_period', 'employee_id', 'pay_period_id'),
        Index('idx_payslip_status', 'status', 'pay_period_id'),
    )
