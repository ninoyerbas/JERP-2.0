"""
JERP 2.0 - Finance Models
Chart of accounts and journal entries with GAAP/IFRS validation
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChartOfAccounts(Base):
    """Chart of accounts with GAAP/IFRS classification"""
    __tablename__ = "chart_of_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(50), unique=True, nullable=False)
    account_name = Column(String(200), nullable=False)
    account_type = Column(String(50))  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    account_subtype = Column(String(100))  # CURRENT_ASSET, FIXED_ASSET, etc.
    parent_account_id = Column(Integer, ForeignKey("chart_of_accounts.id"))
    normal_balance = Column(String(10))  # DEBIT, CREDIT
    is_active = Column(Boolean, default=True)
    gaap_category = Column(String(100))
    ifrs_category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("ChartOfAccounts", remote_side=[id], foreign_keys=[parent_account_id], back_populates="children")
    children = relationship("ChartOfAccounts", back_populates="parent", foreign_keys=[parent_account_id])
    journal_lines = relationship("JournalEntryLine", back_populates="account")


class JournalEntry(Base):
    """Journal entries with automatic GAAP/IFRS validation"""
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_number = Column(String(50), unique=True, nullable=False)
    entry_date = Column(Date, nullable=False)
    posting_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(200))
    
    # Compliance
    gaap_compliant = Column(Boolean, default=True)
    ifrs_compliant = Column(Boolean, default=True)
    validation_notes = Column(Text)
    
    # Status
    status = Column(String(20))  # DRAFT, POSTED, REVERSED
    posted_by = Column(Integer, ForeignKey("users.id"))
    posted_at = Column(DateTime)
    
    # Audit
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    poster = relationship("User", foreign_keys=[posted_by])


class JournalEntryLine(Base):
    """Journal entry line items"""
    __tablename__ = "journal_entry_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    description = Column(Text)
    debit = Column(DECIMAL(15, 2), default=0)
    credit = Column(DECIMAL(15, 2), default=0)
    line_number = Column(Integer)
    
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartOfAccounts", back_populates="journal_lines")
