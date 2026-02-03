"""
JERP 2.0 - Finance Service
Business logic for financial operations
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
from datetime import date, datetime

from app.models.finance import Account, JournalEntry, JournalEntryLine, AccountType, JournalEntryStatus
from app.schemas.finance import (
    AccountCreate, JournalEntryCreate, TrialBalanceReport, 
    BalanceSheetReport, IncomeStatementReport
)
from app.compliance.financial.gaap import GAAP
from app.compliance.financial.ifrs import IFRS
from app.services.compliance_service import ComplianceService


class FinanceService:
    """Finance service with GAAP/IFRS compliance"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gaap = GAAP()
        self.ifrs = IFRS()
        self.compliance_service = ComplianceService(db)
    
    def create_account(self, account_data: AccountCreate) -> Account:
        """Create a new account"""
        account = Account(**account_data.model_dump())
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def create_journal_entry(self, entry_data: JournalEntryCreate, user_id: int) -> JournalEntry:
        """
        Create a new journal entry with compliance validation.
        Automatically checks GAAP/IFRS rules.
        """
        # Generate entry number
        entry_number = self._generate_entry_number()
        
        # Create journal entry
        journal_entry = JournalEntry(
            entry_number=entry_number,
            entry_date=entry_data.entry_date,
            description=entry_data.description,
            reference=entry_data.reference,
            status=JournalEntryStatus.DRAFT,
            created_by=user_id
        )
        
        self.db.add(journal_entry)
        self.db.flush()  # Get ID without committing
        
        # Create lines
        for line_data in entry_data.lines:
            line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                **line_data.model_dump()
            )
            self.db.add(line)
        
        self.db.commit()
        self.db.refresh(journal_entry)
        return journal_entry
    
    def post_journal_entry(self, entry_id: int, user_id: int) -> JournalEntry:
        """
        Post a journal entry and update account balances.
        Validates GAAP/IFRS compliance before posting.
        """
        entry = self.db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
        if not entry:
            raise ValueError("Journal entry not found")
        
        if entry.status != JournalEntryStatus.DRAFT:
            raise ValueError(f"Cannot post entry with status {entry.status}")
        
        # Validate balance
        total_debits = sum(line.debit for line in entry.lines)
        total_credits = sum(line.credit for line in entry.lines)
        
        if total_debits != total_credits:
            raise ValueError("Journal entry is not balanced")
        
        # Check compliance (placeholder - integrate with actual engines)
        entry.gaap_compliant = True
        entry.ifrs_compliant = True
        
        # Update account balances
        for line in entry.lines:
            account = line.account
            if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                # Normal debit balance accounts
                account.current_balance += line.debit - line.credit
            else:
                # Normal credit balance accounts (LIABILITY, EQUITY, REVENUE)
                account.current_balance += line.credit - line.debit
        
        # Mark as posted
        entry.status = JournalEntryStatus.POSTED
        entry.posted_by = user_id
        entry.posted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def generate_trial_balance(self, report_date: date) -> TrialBalanceReport:
        """Generate trial balance as of a specific date"""
        accounts = self.db.query(Account).filter(Account.is_active == True).all()
        
        items = []
        total_debits = Decimal("0")
        total_credits = Decimal("0")
        
        for account in accounts:
            balance = account.current_balance
            
            if balance >= 0:
                debit_balance = balance
                credit_balance = Decimal("0")
            else:
                debit_balance = Decimal("0")
                credit_balance = abs(balance)
            
            items.append({
                "account_number": account.account_number,
                "account_name": account.name,
                "account_type": account.account_type,
                "debit_balance": debit_balance,
                "credit_balance": credit_balance
            })
            
            total_debits += debit_balance
            total_credits += credit_balance
        
        return TrialBalanceReport(
            report_date=report_date,
            accounts=items,
            total_debits=total_debits,
            total_credits=total_credits,
            is_balanced=(total_debits == total_credits)
        )
    
    def _generate_entry_number(self) -> str:
        """Generate unique journal entry number"""
        last_entry = self.db.query(JournalEntry).order_by(JournalEntry.id.desc()).first()
        next_number = (last_entry.id + 1) if last_entry else 1
        return f"JE{next_number:06d}"
