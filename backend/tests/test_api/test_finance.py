"""
JERP 2.0 - Finance API Tests
Tests for account and journal entry endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal

from app.models.user import User
from app.models.role import Role
from app.models.finance import Account, JournalEntry, JournalEntryLine, AccountType, AccountSubtype, JournalEntryStatus


@pytest.fixture
def test_accounts(db: Session):
    """Create test accounts for journal entries"""
    # Create Cash account (Asset)
    cash_account = Account(
        account_number="1000",
        name="Cash",
        description="Cash account",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubtype.CURRENT_ASSET,
        is_active=True,
        current_balance=Decimal("0")
    )
    db.add(cash_account)
    
    # Create Capital account (Equity)
    capital_account = Account(
        account_number="3000",
        name="Owner's Capital",
        description="Owner's equity account",
        account_type=AccountType.EQUITY,
        account_subtype=AccountSubtype.OWNERS_EQUITY,
        is_active=True,
        current_balance=Decimal("0")
    )
    db.add(capital_account)
    
    db.commit()
    db.refresh(cash_account)
    db.refresh(capital_account)
    
    return {"cash": cash_account, "capital": capital_account}


@pytest.fixture
def admin_user(db: Session):
    """Create admin user for testing"""
    from app.core.security import get_password_hash
    
    # Create admin role
    admin_role = Role(
        name="Admin",
        description="Administrator role",
        is_active=True
    )
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)
    
    # Create admin user
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True,
        role_id=admin_role.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(client: TestClient, admin_user: User):
    """Get authentication headers for testing"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": admin_user.email,
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Account Tests

def test_create_account(client: TestClient, auth_headers: dict):
    """Test creating a new account"""
    response = client.post(
        "/api/v1/finance/accounts",
        json={
            "account_number": "1100",
            "name": "Accounts Receivable",
            "description": "Customer receivables",
            "account_type": "ASSET",
            "account_subtype": "CURRENT_ASSET",
            "is_active": True
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["account_number"] == "1100"
    assert data["name"] == "Accounts Receivable"
    assert data["account_type"] == "ASSET"
    assert data["current_balance"] == "0.00"


def test_list_accounts(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test listing accounts"""
    response = client.get(
        "/api/v1/finance/accounts",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least the two test accounts
    
    # Check that our test accounts are in the list
    account_numbers = [acc["account_number"] for acc in data]
    assert "1000" in account_numbers  # Cash
    assert "3000" in account_numbers  # Capital


def test_list_accounts_filter_by_type(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test listing accounts filtered by type"""
    response = client.get(
        "/api/v1/finance/accounts?account_type=ASSET",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned accounts should be assets
    for account in data:
        assert account["account_type"] == "ASSET"


def test_get_account(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test getting a specific account"""
    account_id = test_accounts["cash"].id
    
    response = client.get(
        f"/api/v1/finance/accounts/{account_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == account_id
    assert data["account_number"] == "1000"
    assert data["name"] == "Cash"


def test_get_nonexistent_account(client: TestClient, auth_headers: dict):
    """Test getting a non-existent account"""
    response = client.get(
        "/api/v1/finance/accounts/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_update_account(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test updating an account"""
    account_id = test_accounts["cash"].id
    
    response = client.put(
        f"/api/v1/finance/accounts/{account_id}",
        json={
            "name": "Cash - Main Account",
            "description": "Primary cash account"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cash - Main Account"
    assert data["description"] == "Primary cash account"


def test_update_nonexistent_account(client: TestClient, auth_headers: dict):
    """Test updating a non-existent account"""
    response = client.put(
        "/api/v1/finance/accounts/99999",
        json={"name": "Updated Name"},
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_delete_account_with_transactions(client: TestClient, auth_headers: dict, test_accounts: dict, db: Session, admin_user: User):
    """Test that deleting an account with transactions fails"""
    # Create a journal entry with the account
    from app.services.finance_service import FinanceService
    from app.schemas.finance import JournalEntryCreate, JournalEntryLineCreate
    
    service = FinanceService(db)
    entry_data = JournalEntryCreate(
        entry_date=date.today(),
        description="Test entry",
        lines=[
            JournalEntryLineCreate(
                account_id=test_accounts["cash"].id,
                debit=Decimal("100"),
                credit=Decimal("0")
            ),
            JournalEntryLineCreate(
                account_id=test_accounts["capital"].id,
                debit=Decimal("0"),
                credit=Decimal("100")
            )
        ]
    )
    service.create_journal_entry(entry_data, admin_user.id)
    
    # Try to delete the account
    response = client.delete(
        f"/api/v1/finance/accounts/{test_accounts['cash'].id}",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "existing transactions" in response.json()["detail"].lower()


def test_delete_account_without_transactions(client: TestClient, auth_headers: dict, db: Session):
    """Test deleting an account without transactions"""
    # Create a new account without transactions
    from app.models.finance import Account, AccountType, AccountSubtype
    
    account = Account(
        account_number="9999",
        name="Temporary Account",
        account_type=AccountType.EXPENSE,
        account_subtype=AccountSubtype.OPERATING_EXPENSE,
        is_active=True
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    
    # Delete it
    response = client.delete(
        f"/api/v1/finance/accounts/{account.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify it's deleted
    deleted = db.query(Account).filter(Account.id == account.id).first()
    assert deleted is None


# Journal Entry Tests

def test_create_journal_entry(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test creating a new journal entry"""
    response = client.post(
        "/api/v1/finance/journal-entries",
        json={
            "entry_date": str(date.today()),
            "description": "Initial capital investment",
            "reference": "INV-001",
            "lines": [
                {
                    "account_id": test_accounts["cash"].id,
                    "debit": "10000.00",
                    "credit": "0.00",
                    "description": "Cash received"
                },
                {
                    "account_id": test_accounts["capital"].id,
                    "debit": "0.00",
                    "credit": "10000.00",
                    "description": "Capital contribution"
                }
            ]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Initial capital investment"
    assert data["status"] == "DRAFT"
    assert len(data["lines"]) == 2
    assert data["entry_number"].startswith("JE")


def test_create_unbalanced_journal_entry(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test that unbalanced journal entry is rejected"""
    response = client.post(
        "/api/v1/finance/journal-entries",
        json={
            "entry_date": str(date.today()),
            "description": "Unbalanced entry",
            "lines": [
                {
                    "account_id": test_accounts["cash"].id,
                    "debit": "5000.00",
                    "credit": "0.00"
                },
                {
                    "account_id": test_accounts["capital"].id,
                    "debit": "0.00",
                    "credit": "3000.00"  # Not balanced!
                }
            ]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert "balanced" in response.json()["detail"][0]["msg"].lower()


def test_create_journal_entry_single_line(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test that journal entry with single line is rejected"""
    response = client.post(
        "/api/v1/finance/journal-entries",
        json={
            "entry_date": str(date.today()),
            "description": "Single line entry",
            "lines": [
                {
                    "account_id": test_accounts["cash"].id,
                    "debit": "1000.00",
                    "credit": "0.00"
                }
            ]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422


def test_create_journal_entry_both_debit_credit(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test that journal entry line with both debit and credit is rejected"""
    response = client.post(
        "/api/v1/finance/journal-entries",
        json={
            "entry_date": str(date.today()),
            "description": "Invalid line entry",
            "lines": [
                {
                    "account_id": test_accounts["cash"].id,
                    "debit": "1000.00",
                    "credit": "500.00"  # Both values - invalid!
                },
                {
                    "account_id": test_accounts["capital"].id,
                    "debit": "0.00",
                    "credit": "1500.00"
                }
            ]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422


def test_create_journal_entry_zero_amounts(client: TestClient, auth_headers: dict, test_accounts: dict):
    """Test that journal entry line with zero amounts is rejected"""
    response = client.post(
        "/api/v1/finance/journal-entries",
        json={
            "entry_date": str(date.today()),
            "description": "Zero amount line entry",
            "lines": [
                {
                    "account_id": test_accounts["cash"].id,
                    "debit": "0.00",
                    "credit": "0.00"  # Both zero - invalid!
                },
                {
                    "account_id": test_accounts["capital"].id,
                    "debit": "0.00",
                    "credit": "0.00"
                }
            ]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422


def test_list_journal_entries(client: TestClient, auth_headers: dict, test_accounts: dict, db: Session, admin_user: User):
    """Test listing journal entries"""
    # Create a journal entry first
    from app.services.finance_service import FinanceService
    from app.schemas.finance import JournalEntryCreate, JournalEntryLineCreate
    
    service = FinanceService(db)
    entry_data = JournalEntryCreate(
        entry_date=date.today(),
        description="Test entry",
        lines=[
            JournalEntryLineCreate(
                account_id=test_accounts["cash"].id,
                debit=Decimal("1000"),
                credit=Decimal("0")
            ),
            JournalEntryLineCreate(
                account_id=test_accounts["capital"].id,
                debit=Decimal("0"),
                credit=Decimal("1000")
            )
        ]
    )
    service.create_journal_entry(entry_data, admin_user.id)
    
    # Now test listing
    response = client.get(
        "/api/v1/finance/journal-entries",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_post_journal_entry(client: TestClient, auth_headers: dict, test_accounts: dict, db: Session, admin_user: User):
    """Test posting a journal entry"""
    # Create a journal entry
    from app.services.finance_service import FinanceService
    from app.schemas.finance import JournalEntryCreate, JournalEntryLineCreate
    
    service = FinanceService(db)
    entry_data = JournalEntryCreate(
        entry_date=date.today(),
        description="Test entry for posting",
        lines=[
            JournalEntryLineCreate(
                account_id=test_accounts["cash"].id,
                debit=Decimal("2000"),
                credit=Decimal("0")
            ),
            JournalEntryLineCreate(
                account_id=test_accounts["capital"].id,
                debit=Decimal("0"),
                credit=Decimal("2000")
            )
        ]
    )
    entry = service.create_journal_entry(entry_data, admin_user.id)
    
    # Check initial balances
    db.refresh(test_accounts["cash"])
    db.refresh(test_accounts["capital"])
    initial_cash = test_accounts["cash"].current_balance
    initial_capital = test_accounts["capital"].current_balance
    
    # Post the entry
    response = client.post(
        f"/api/v1/finance/journal-entries/{entry.id}/post",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "POSTED"
    assert data["posted_by"] == admin_user.id
    assert data["posted_at"] is not None
    
    # Verify balances were updated
    db.refresh(test_accounts["cash"])
    db.refresh(test_accounts["capital"])
    assert test_accounts["cash"].current_balance == initial_cash + Decimal("2000")
    assert test_accounts["capital"].current_balance == initial_capital + Decimal("2000")


def test_post_already_posted_entry(client: TestClient, auth_headers: dict, test_accounts: dict, db: Session, admin_user: User):
    """Test that posting an already posted entry fails"""
    # Create and post a journal entry
    from app.services.finance_service import FinanceService
    from app.schemas.finance import JournalEntryCreate, JournalEntryLineCreate
    
    service = FinanceService(db)
    entry_data = JournalEntryCreate(
        entry_date=date.today(),
        description="Test entry",
        lines=[
            JournalEntryLineCreate(
                account_id=test_accounts["cash"].id,
                debit=Decimal("500"),
                credit=Decimal("0")
            ),
            JournalEntryLineCreate(
                account_id=test_accounts["capital"].id,
                debit=Decimal("0"),
                credit=Decimal("500")
            )
        ]
    )
    entry = service.create_journal_entry(entry_data, admin_user.id)
    service.post_journal_entry(entry.id, admin_user.id)
    
    # Try to post again
    response = client.post(
        f"/api/v1/finance/journal-entries/{entry.id}/post",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Cannot post" in response.json()["detail"]


# Financial Reports Tests

def test_generate_trial_balance(client: TestClient, auth_headers: dict, test_accounts: dict, db: Session, admin_user: User):
    """Test generating trial balance report"""
    # Create and post some entries to have balances
    from app.services.finance_service import FinanceService
    from app.schemas.finance import JournalEntryCreate, JournalEntryLineCreate
    
    service = FinanceService(db)
    entry_data = JournalEntryCreate(
        entry_date=date.today(),
        description="Test entry for trial balance",
        lines=[
            JournalEntryLineCreate(
                account_id=test_accounts["cash"].id,
                debit=Decimal("5000"),
                credit=Decimal("0")
            ),
            JournalEntryLineCreate(
                account_id=test_accounts["capital"].id,
                debit=Decimal("0"),
                credit=Decimal("5000")
            )
        ]
    )
    entry = service.create_journal_entry(entry_data, admin_user.id)
    service.post_journal_entry(entry.id, admin_user.id)
    
    # Get trial balance
    response = client.get(
        f"/api/v1/finance/reports/trial-balance?report_date={date.today()}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert "total_debits" in data
    assert "total_credits" in data
    assert "is_balanced" in data
    assert data["is_balanced"] is True
    assert len(data["accounts"]) >= 2


def test_trial_balance_authentication_required(client: TestClient):
    """Test that trial balance requires authentication"""
    response = client.get("/api/v1/finance/reports/trial-balance")
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
