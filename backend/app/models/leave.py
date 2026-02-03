"""
JERP 2.0 - Leave Management Models
Leave policies, balances, and requests
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.core.database import Base


class LeavePolicy(Base):
    """Leave policies (PTO, Sick, etc.)"""
    __tablename__ = "leave_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    leave_type = Column(String(50))  # PTO, SICK, VACATION, UNPAID
    accrual_rate = Column(DECIMAL(10, 4))  # Hours per pay period
    max_balance = Column(DECIMAL(10, 2))
    carry_over_allowed = Column(Boolean, default=True)
    max_carry_over = Column(DECIMAL(10, 2))
    requires_approval = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    balances = relationship("LeaveBalance", back_populates="policy")
    requests = relationship("LeaveRequest", back_populates="policy")


class LeaveBalance(Base):
    """Employee leave balances"""
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("leave_policies.id"), nullable=False)
    available_hours = Column(DECIMAL(10, 2), default=0)
    pending_hours = Column(DECIMAL(10, 2), default=0)
    used_hours = Column(DECIMAL(10, 2), default=0)
    last_accrual_date = Column(Date)
    
    employee = relationship("Employee")
    policy = relationship("LeavePolicy", back_populates="balances")


class LeaveRequest(Base):
    """Leave requests with approval workflow"""
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("leave_policies.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    hours_requested = Column(DECIMAL(10, 2), nullable=False)
    reason = Column(Text)
    status = Column(String(20))  # PENDING, APPROVED, REJECTED, CANCELLED
    
    # Approval
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    employee = relationship("Employee", back_populates="leave_requests")
    policy = relationship("LeavePolicy", back_populates="requests")
    reviewer = relationship("User")
