"""
JERP 2.0 - Time & Attendance Models
Employee timesheets with automatic compliance checking
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.core.database import Base


class Timesheet(Base):
    """Employee timesheets with automatic compliance checking"""
    __tablename__ = "timesheets"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String(20))  # DRAFT, SUBMITTED, APPROVED, REJECTED
    
    # Hours
    regular_hours = Column(DECIMAL(10, 2), default=0)
    overtime_hours = Column(DECIMAL(10, 2), default=0)
    double_time_hours = Column(DECIMAL(10, 2), default=0)
    pto_hours = Column(DECIMAL(10, 2), default=0)
    
    # Compliance
    is_seventh_consecutive_day = Column(Boolean, default=False)
    meal_breaks_compliant = Column(Boolean, default=True)
    rest_breaks_compliant = Column(Boolean, default=True)
    
    # Approval
    submitted_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    employee = relationship("Employee", back_populates="timesheets")
    approver = relationship("User")
    entries = relationship("TimesheetEntry", back_populates="timesheet", cascade="all, delete-orphan")


class TimesheetEntry(Base):
    """Daily timesheet entries"""
    __tablename__ = "timesheet_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id"), nullable=False)
    work_date = Column(Date, nullable=False)
    clock_in = Column(DateTime)
    clock_out = Column(DateTime)
    hours_worked = Column(DECIMAL(10, 2))
    break_minutes = Column(Integer, default=0)
    notes = Column(Text)
    
    timesheet = relationship("Timesheet", back_populates="entries")
    breaks = relationship("BreakEntry", back_populates="entry", cascade="all, delete-orphan")


class BreakEntry(Base):
    """Break tracking for California Labor Code compliance"""
    __tablename__ = "break_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    timesheet_entry_id = Column(Integer, ForeignKey("timesheet_entries.id"), nullable=False)
    break_type = Column(String(20))  # MEAL, REST
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    
    entry = relationship("TimesheetEntry", back_populates="breaks")
