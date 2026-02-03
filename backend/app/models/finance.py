"""
JERP 2.0 - Finance Models
Chart of Accounts, Journal Entries, and Financial Transactions
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Numeric, Text, Enum as SQLEnum, Index, CheckConstraint
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class AccountType(str, enum.Enum):
    """Account type enumeration"""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AccountSubtype(str, enum.Enum):
    """Account subtype enumeration"""
    # Assets
    CURRENT_ASSET = "CURRENT_ASSET"
    FIXED_ASSET = "FIXED_ASSET"
    OTHER_ASSET = "OTHER_ASSET"
    
    # Liabilities
    CURRENT_LIABILITY = "CURRENT_LIABILITY"
    LONG_TERM_LIABILITY = "LONG_TERM_LIABILITY"
    
    # Equity
    OWNERS_EQUITY = "OWNERS_EQUITY"
    RETAINED_EARNINGS = "RETAINED_EARNINGS"
    
    # Revenue
    OPERATING_REVENUE = "OPERATING_REVENUE"
    NON_OPERATING_REVENUE = "NON_OPERATING_REVENUE"
    
    # Expenses
    OPERATING_EXPENSE = "OPERATING_EXPENSE"
    COST_OF_GOODS_SOLD = "COST_OF_GOODS_SOLD"
    NON_OPERATING_EXPENSE = "NON_OPERATING_EXPENSE"


class JournalEntryStatus(str, enum.Enum):
    """Journal entry status"""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    VOID = "VOID"


class Account(Base):
    """Chart of Accounts"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Account identification
    account_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Account classification
    account_type = Column(SQLEnum(AccountType), nullable=False, index=True)
    account_subtype = Column(SQLEnum(AccountSubtype), nullable=False, index=True)
    
    # Hierarchy support
    parent_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)
    parent_account = relationship("Account", remote_side=[id], backref="sub_accounts")
    
    # Properties
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_account = Column(Boolean, default=False, nullable=False)  # Cannot be deleted
    
    # Balance tracking
    current_balance = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Department linkage (optional)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    department = relationship("Department")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    journal_entry_lines = relationship("JournalEntryLine", back_populates="account")

    def __repr__(self):
        return f"<Account(number='{self.account_number}', name='{self.name}', balance={self.current_balance})>"

    __table_args__ = (
        Index('idx_account_type_active', 'account_type', 'is_active'),
    )


class JournalEntry(Base):
    """Journal Entry header"""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Entry identification
    entry_number = Column(String(50), unique=True, index=True, nullable=False)
    entry_date = Column(Date, nullable=False, index=True)
    
    # Description
    description = Column(Text, nullable=False)
    reference = Column(String(100), nullable=True, index=True)  # External reference (invoice #, etc.)
    
    # Status
    status = Column(SQLEnum(JournalEntryStatus), default=JournalEntryStatus.DRAFT, nullable=False, index=True)
    
    # Posting information
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    posted_by_user = relationship("User", foreign_keys=[posted_by])
    posted_at = Column(DateTime, nullable=True)
    
    # Compliance tracking
    gaap_compliant = Column(Boolean, default=True, nullable=False)
    ifrs_compliant = Column(Boolean, default=True, nullable=False)
    compliance_notes = Column(Text, nullable=True)
    
    # Audit
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User", foreign_keys=[created_by])
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JournalEntry(number='{self.entry_number}', date={self.entry_date}, status={self.status})>"

    __table_args__ = (
        Index('idx_entry_date_status', 'entry_date', 'status'),
    )


class JournalEntryLine(Base):
    """Journal Entry line items (debits and credits)"""
    __tablename__ = "journal_entry_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Parent journal entry
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False, index=True)
    journal_entry = relationship("JournalEntry", back_populates="lines")
    
    # Account
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    account = relationship("Account", back_populates="journal_entry_lines")
    
    # Amounts (one must be zero)
    debit = Column(Numeric(15, 2), default=0, nullable=False)
    credit = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Department allocation (optional)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    department = relationship("Department")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<JournalEntryLine(account_id={self.account_id}, debit={self.debit}, credit={self.credit})>"

    __table_args__ = (
        CheckConstraint('(debit > 0 AND credit = 0) OR (debit = 0 AND credit > 0)', name='check_debit_or_credit'),
        Index('idx_journal_line_account', 'journal_entry_id', 'account_id'),
    )
