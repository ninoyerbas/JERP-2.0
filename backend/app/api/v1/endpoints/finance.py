"""
JERP 2.0 - Finance Management Endpoints
Chart of accounts, journal entries, and financial reports
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.finance import Account, JournalEntry, AccountType, JournalEntryStatus
from app.schemas.finance import (
    AccountCreate, AccountUpdate, AccountResponse,
    JournalEntryCreate, JournalEntryResponse, JournalEntryWithDetails,
    TrialBalanceReport, BalanceSheetReport, IncomeStatementReport
)
from app.services.finance_service import FinanceService

router = APIRouter()


# Chart of Accounts Endpoints

@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    account_type: Optional[AccountType] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all accounts with filtering"""
    query = db.query(Account)
    
    if account_type:
        query = query.filter(Account.account_type == account_type)
    
    if is_active is not None:
        query = query.filter(Account.is_active == is_active)
    
    accounts = query.offset(skip).limit(limit).all()
    return accounts


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new account"""
    service = FinanceService(db)
    account = service.create_account(account_data)
    return account


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get account by ID"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check if it's a system account
    if account.is_system_account and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system accounts"
        )
    
    # Update fields
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an account (only if no transactions exist)"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check if it's a system account
    if account.is_system_account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system accounts"
        )
    
    # Check for existing transactions
    from app.models.finance import JournalEntryLine
    has_transactions = db.query(JournalEntryLine).filter(
        JournalEntryLine.account_id == account_id
    ).first() is not None
    
    if has_transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete account with existing transactions. Deactivate it instead."
        )
    
    db.delete(account)
    db.commit()


# Journal Entry Endpoints

@router.get("/journal-entries", response_model=List[JournalEntryResponse])
async def list_journal_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    entry_status: Optional[JournalEntryStatus] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List journal entries with filtering"""
    query = db.query(JournalEntry)
    
    if entry_status:
        query = query.filter(JournalEntry.status == entry_status)
    
    if start_date:
        query = query.filter(JournalEntry.entry_date >= start_date)
    
    if end_date:
        query = query.filter(JournalEntry.entry_date <= end_date)
    
    entries = query.offset(skip).limit(limit).order_by(JournalEntry.entry_date.desc()).all()
    return entries


@router.post("/journal-entries", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new journal entry (draft status)"""
    service = FinanceService(db)
    entry = service.create_journal_entry(entry_data, current_user.id)
    return entry


@router.get("/journal-entries/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get journal entry by ID"""
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found"
        )
    return entry


@router.post("/journal-entries/{entry_id}/post", response_model=JournalEntryResponse)
async def post_journal_entry(
    entry_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Post a journal entry (updates account balances)"""
    service = FinanceService(db)
    try:
        entry = service.post_journal_entry(entry_id, current_user.id)
        return entry
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Financial Reports Endpoints

@router.get("/reports/trial-balance", response_model=TrialBalanceReport)
async def get_trial_balance(
    report_date: date = Query(default=date.today()),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate trial balance report"""
    service = FinanceService(db)
    report = service.generate_trial_balance(report_date)
    return report
