"""
JERP 2.0 - Finance Schemas
Pydantic models for financial management
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.models.finance import AccountType, AccountSubtype, JournalEntryStatus


# Account Schemas
class AccountBase(BaseModel):
    """Base account fields"""
    account_number: str
    name: str
    description: Optional[str] = None
    account_type: AccountType
    account_subtype: AccountSubtype
    parent_account_id: Optional[int] = None
    department_id: Optional[int] = None
    is_active: bool = True


class AccountCreate(AccountBase):
    """Account creation request"""
    pass


class AccountUpdate(BaseModel):
    """Account update request - all fields optional"""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_account_id: Optional[int] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    """Account response with all fields"""
    id: int
    current_balance: Decimal
    is_system_account: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Journal Entry Line Schemas
class JournalEntryLineBase(BaseModel):
    """Base journal entry line fields"""
    account_id: int
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: Optional[str] = None
    department_id: Optional[int] = None

    @field_validator('debit', 'credit')
    @classmethod
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return v


class JournalEntryLineCreate(JournalEntryLineBase):
    """Journal entry line creation"""
    pass


class JournalEntryLineResponse(JournalEntryLineBase):
    """Journal entry line response"""
    id: int
    journal_entry_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Journal Entry Schemas
class JournalEntryBase(BaseModel):
    """Base journal entry fields"""
    entry_date: date
    description: str
    reference: Optional[str] = None


class JournalEntryCreate(JournalEntryBase):
    """Journal entry creation request"""
    lines: List[JournalEntryLineCreate] = Field(..., min_length=2)

    @field_validator('lines')
    @classmethod
    def validate_balanced_entry(cls, v):
        total_debits = sum(line.debit for line in v)
        total_credits = sum(line.credit for line in v)
        
        if total_debits != total_credits:
            raise ValueError(f'Journal entry must be balanced. Debits: {total_debits}, Credits: {total_credits}')
        
        if total_debits == 0:
            raise ValueError('Journal entry cannot have zero amount')
        
        return v


class JournalEntryResponse(JournalEntryBase):
    """Journal entry response"""
    id: int
    entry_number: str
    status: JournalEntryStatus
    posted_by: Optional[int]
    posted_at: Optional[datetime]
    gaap_compliant: bool
    ifrs_compliant: bool
    compliance_notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    lines: List[JournalEntryLineResponse] = []
    
    class Config:
        from_attributes = True


class JournalEntryWithDetails(JournalEntryResponse):
    """Journal entry with account details"""
    pass


# Financial Report Schemas
class TrialBalanceItem(BaseModel):
    """Trial balance line item"""
    account_number: str
    account_name: str
    account_type: AccountType
    debit_balance: Decimal
    credit_balance: Decimal


class TrialBalanceReport(BaseModel):
    """Trial balance report"""
    report_date: date
    accounts: List[TrialBalanceItem]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


class BalanceSheetItem(BaseModel):
    """Balance sheet line item"""
    account_number: str
    account_name: str
    amount: Decimal


class BalanceSheetReport(BaseModel):
    """Balance sheet report"""
    report_date: date
    assets: List[BalanceSheetItem]
    liabilities: List[BalanceSheetItem]
    equity: List[BalanceSheetItem]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    is_balanced: bool


class IncomeStatementItem(BaseModel):
    """Income statement line item"""
    account_number: str
    account_name: str
    amount: Decimal


class IncomeStatementReport(BaseModel):
    """Income statement report"""
    start_date: date
    end_date: date
    revenue: List[IncomeStatementItem]
    expenses: List[IncomeStatementItem]
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
