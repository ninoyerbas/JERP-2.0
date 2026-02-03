"""
JERP 2.0 - Finance Schemas
Pydantic models for Finance module
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Chart of Accounts Schemas
class ChartOfAccountsBase(BaseModel):
    account_number: str = Field(..., max_length=50)
    account_name: str = Field(..., max_length=200)
    account_type: str = Field(..., max_length=50)  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    account_subtype: Optional[str] = Field(None, max_length=100)
    parent_account_id: Optional[int] = None
    normal_balance: str = Field(..., max_length=10)  # DEBIT, CREDIT
    is_active: bool = True
    gaap_category: Optional[str] = Field(None, max_length=100)
    ifrs_category: Optional[str] = Field(None, max_length=100)


class ChartOfAccountsCreate(ChartOfAccountsBase):
    pass


class ChartOfAccountsUpdate(BaseModel):
    account_name: Optional[str] = Field(None, max_length=200)
    account_type: Optional[str] = Field(None, max_length=50)
    account_subtype: Optional[str] = Field(None, max_length=100)
    parent_account_id: Optional[int] = None
    normal_balance: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None
    gaap_category: Optional[str] = Field(None, max_length=100)
    ifrs_category: Optional[str] = Field(None, max_length=100)


class ChartOfAccountsResponse(ChartOfAccountsBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChartOfAccountsList(BaseModel):
    total: int
    items: List[ChartOfAccountsResponse]


# Journal Entry Line Schemas
class JournalEntryLineBase(BaseModel):
    account_id: int
    description: Optional[str] = None
    debit: Decimal = Field(default=Decimal("0"))
    credit: Decimal = Field(default=Decimal("0"))
    line_number: Optional[int] = None


class JournalEntryLineCreate(JournalEntryLineBase):
    pass


class JournalEntryLineResponse(JournalEntryLineBase):
    id: int
    entry_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Journal Entry Schemas
class JournalEntryBase(BaseModel):
    entry_number: str = Field(..., max_length=50)
    entry_date: date
    posting_date: date
    description: str
    reference: Optional[str] = Field(None, max_length=200)


class JournalEntryCreate(JournalEntryBase):
    lines: List[JournalEntryLineCreate]


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[date] = None
    posting_date: Optional[date] = None
    description: Optional[str] = None
    reference: Optional[str] = Field(None, max_length=200)


class JournalEntryResponse(JournalEntryBase):
    id: int
    gaap_compliant: bool
    ifrs_compliant: bool
    validation_notes: Optional[str] = None
    status: str
    posted_by: Optional[int] = None
    posted_at: Optional[datetime] = None
    created_by: int
    created_at: datetime
    lines: List[JournalEntryLineResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class JournalEntryList(BaseModel):
    total: int
    items: List[JournalEntryResponse]


# Journal Entry Posting Request
class PostJournalEntryRequest(BaseModel):
    standard: str  # GAAP or IFRS


# Journal Entry Posting Response
class PostJournalEntryResponse(BaseModel):
    success: bool
    compliant: bool
    violations: List[str] = []


# Balance Sheet
class BalanceSheetResponse(BaseModel):
    as_of_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    is_balanced: bool
    accounts: List[dict]


# Income Statement
class IncomeStatementResponse(BaseModel):
    start_date: date
    end_date: date
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
    accounts: List[dict]


# Compliance Status
class FinanceComplianceStatus(BaseModel):
    total_entries: int
    gaap_compliant_entries: int
    ifrs_compliant_entries: int
    gaap_violations: int
    ifrs_violations: int
    compliance_rate: float
