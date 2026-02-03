"""
Tests for GAAP Validation Engine
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.compliance import gaap


class TestBalanceSheet:
    """Test balance sheet validation"""
    
    def test_balanced_sheet(self):
        """Test balanced balance sheet"""
        assets = {
            "Cash": Decimal("50000"),
            "Accounts Receivable": Decimal("30000"),
            "Equipment": Decimal("100000")
        }
        liabilities = {
            "Accounts Payable": Decimal("20000"),
            "Notes Payable": Decimal("50000")
        }
        equity = {
            "Common Stock": Decimal("100000"),
            "Retained Earnings": Decimal("10000")
        }
        
        result = gaap.validate_balance_sheet(assets, liabilities, equity)
        
        assert result["compliant"] is True
        assert result["total_assets"] == 180000.0
        assert result["total_liabilities"] == 70000.0
        assert result["total_equity"] == 110000.0
        assert abs(result["balance"]) <= 0.01
    
    def test_imbalanced_sheet(self):
        """Test imbalanced balance sheet"""
        assets = {"Cash": Decimal("100000")}
        liabilities = {"Accounts Payable": Decimal("20000")}
        equity = {"Common Stock": Decimal("50000")}
        
        result = gaap.validate_balance_sheet(assets, liabilities, equity)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "BALANCE_SHEET_IMBALANCE"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"


class TestJournalEntry:
    """Test journal entry validation"""
    
    def test_balanced_entry(self):
        """Test balanced journal entry"""
        entry = {
            "date": "2024-01-15",
            "description": "Record accounts receivable payment",
            "debits": [
                {"account": "Cash", "amount": 5000.00}
            ],
            "credits": [
                {"account": "Accounts Receivable", "amount": 5000.00}
            ]
        }
        
        result = gaap.validate_journal_entry(entry)
        
        assert result["compliant"] is True
        assert result["total_debits"] == 5000.0
        assert result["total_credits"] == 5000.0
        assert abs(result["balance"]) <= 0.01
    
    def test_unbalanced_entry(self):
        """Test unbalanced journal entry"""
        entry = {
            "date": "2024-01-15",
            "description": "Unbalanced entry",
            "debits": [
                {"account": "Cash", "amount": 5000.00}
            ],
            "credits": [
                {"account": "Accounts Receivable", "amount": 4000.00}
            ]
        }
        
        result = gaap.validate_journal_entry(entry)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "UNBALANCED_ENTRY"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"
    
    def test_no_debits(self):
        """Test entry with no debits"""
        entry = {
            "date": "2024-01-15",
            "description": "Missing debits",
            "debits": [],
            "credits": [
                {"account": "Revenue", "amount": 1000.00}
            ]
        }
        
        result = gaap.validate_journal_entry(entry)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "NO_DEBITS"]
        assert len(violations) == 1
    
    def test_future_date(self):
        """Test entry with future date"""
        future_date = (datetime.now().replace(microsecond=0) + timedelta(days=1)).isoformat()
        
        entry = {
            "date": future_date,
            "description": "Future dated entry",
            "debits": [{"account": "Cash", "amount": 1000}],
            "credits": [{"account": "Revenue", "amount": 1000}]
        }
        
        result = gaap.validate_journal_entry(entry)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "FUTURE_DATE"]
        assert len(violations) == 1


class TestRevenueRecognition:
    """Test revenue recognition (ASC 606)"""
    
    def test_valid_revenue_recognition(self):
        """Test valid revenue recognition"""
        transaction = {
            "contract_id": "C-12345",
            "transaction_price": 10000,
            "performance_obligations": [
                {
                    "description": "Product delivery",
                    "allocated_price": 7000,
                    "is_satisfied": True,
                    "satisfaction_date": "2024-01-15"
                },
                {
                    "description": "Installation",
                    "allocated_price": 3000,
                    "is_satisfied": True,
                    "satisfaction_date": "2024-01-20"
                }
            ]
        }
        
        result = gaap.validate_revenue_recognition(transaction)
        
        assert result["compliant"] is True
        assert result["revenue_recognizable"] == 10000.0
    
    def test_no_contract(self):
        """Test revenue recognition without contract"""
        transaction = {
            "transaction_price": 5000,
            "performance_obligations": []
        }
        
        result = gaap.validate_revenue_recognition(transaction)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "NO_CONTRACT"]
        assert len(violations) == 1
    
    def test_partial_satisfaction(self):
        """Test partial performance obligation satisfaction"""
        transaction = {
            "contract_id": "C-12345",
            "transaction_price": 10000,
            "performance_obligations": [
                {
                    "allocated_price": 10000,
                    "is_satisfied": False
                }
            ]
        }
        
        result = gaap.validate_revenue_recognition(transaction)
        
        # Should be compliant but revenue recognizable is 0
        assert result["revenue_recognizable"] == 0.0


class TestDepreciation:
    """Test depreciation calculation"""
    
    def test_straight_line_depreciation(self):
        """Test straight-line depreciation"""
        asset = {
            "cost": 100000,
            "salvage_value": 10000,
            "useful_life_years": 10,
            "accumulated_depreciation": 0
        }
        
        result = gaap.validate_depreciation(asset, "straight-line")
        
        assert result["compliant"] is True
        assert result["annual_depreciation"] == 9000.0  # (100000 - 10000) / 10
    
    def test_double_declining_balance(self):
        """Test double declining balance depreciation"""
        asset = {
            "cost": 100000,
            "salvage_value": 10000,
            "useful_life_years": 5,
            "accumulated_depreciation": 0
        }
        
        result = gaap.validate_depreciation(asset, "double-declining")
        
        assert result["compliant"] is True
        # Year 1: 100000 * (2/5) = 40000
        assert result["annual_depreciation"] == 40000.0
    
    def test_invalid_cost(self):
        """Test depreciation with invalid cost"""
        asset = {
            "cost": 0,
            "salvage_value": 1000,
            "useful_life_years": 5,
            "accumulated_depreciation": 0
        }
        
        result = gaap.validate_depreciation(asset, "straight-line")
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "INVALID_COST"]
        assert len(violations) == 1
    
    def test_salvage_exceeds_cost(self):
        """Test depreciation where salvage value exceeds cost"""
        asset = {
            "cost": 10000,
            "salvage_value": 15000,
            "useful_life_years": 5,
            "accumulated_depreciation": 0
        }
        
        result = gaap.validate_depreciation(asset, "straight-line")
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "SALVAGE_EXCEEDS_COST"]
        assert len(violations) == 1
