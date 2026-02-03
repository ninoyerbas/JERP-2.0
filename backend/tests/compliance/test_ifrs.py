"""
Tests for IFRS Validation Engine
"""
import pytest
from decimal import Decimal
from app.services.compliance import ifrs


class TestIFRS15Revenue:
    """Test IFRS 15 revenue recognition"""
    
    def test_valid_revenue_contract(self):
        """Test valid IFRS 15 revenue recognition"""
        contract = {
            "customer_id": 12345,
            "has_commercial_substance": True,
            "payment_probable": True,
            "transaction_price": 10000,
            "performance_obligations": [
                {
                    "allocated_price": 10000,
                    "satisfaction_method": "point_in_time",
                    "control_transferred": True
                }
            ]
        }
        
        result = ifrs.validate_ifrs15_revenue(contract)
        
        assert result["compliant"] is True
        assert result["revenue_recognizable"] == 10000.0
    
    def test_no_customer(self):
        """Test contract without customer identification"""
        contract = {
            "transaction_price": 5000,
            "performance_obligations": []
        }
        
        result = ifrs.validate_ifrs15_revenue(contract)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "NO_CUSTOMER"]
        assert len(violations) == 1
    
    def test_over_time_recognition(self):
        """Test revenue recognition over time"""
        contract = {
            "customer_id": 12345,
            "has_commercial_substance": True,
            "payment_probable": True,
            "transaction_price": 10000,
            "performance_obligations": [
                {
                    "allocated_price": 10000,
                    "satisfaction_method": "over_time",
                    "progress_percentage": 50
                }
            ]
        }
        
        result = ifrs.validate_ifrs15_revenue(contract)
        
        assert result["compliant"] is True
        assert result["revenue_recognizable"] == 5000.0  # 50% of 10000
    
    def test_invalid_progress(self):
        """Test invalid progress percentage"""
        contract = {
            "customer_id": 12345,
            "has_commercial_substance": True,
            "payment_probable": True,
            "transaction_price": 10000,
            "performance_obligations": [
                {
                    "allocated_price": 10000,
                    "satisfaction_method": "over_time",
                    "progress_percentage": 150  # Invalid: > 100
                }
            ]
        }
        
        result = ifrs.validate_ifrs15_revenue(contract)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "INVALID_PROGRESS"]
        assert len(violations) == 1


class TestIFRS16Lease:
    """Test IFRS 16 lease accounting"""
    
    def test_standard_lease(self):
        """Test standard lease recognition"""
        lease = {
            "lease_term_months": 36,
            "monthly_payment": Decimal("1000"),
            "underlying_asset_value": Decimal("30000"),
            "discount_rate": Decimal("5"),
            "initial_direct_costs": Decimal("500"),
            "prepayments": Decimal("0"),
            "lease_incentives": Decimal("0")
        }
        
        result = ifrs.validate_ifrs16_lease(lease)
        
        assert result["compliant"] is True
        assert result["lease_liability"] > 0
        assert result["right_of_use_asset"] > 0
    
    def test_short_term_exemption(self):
        """Test short-term lease exemption"""
        lease = {
            "lease_term_months": 12,
            "monthly_payment": Decimal("500"),
            "underlying_asset_value": Decimal("5000"),
            "discount_rate": Decimal("5"),
            "short_term_exemption_elected": True
        }
        
        result = ifrs.validate_ifrs16_lease(lease)
        
        assert result.get("exemption") == "short_term"
    
    def test_low_value_exemption(self):
        """Test low-value asset exemption"""
        lease = {
            "lease_term_months": 24,
            "monthly_payment": Decimal("100"),
            "underlying_asset_value": Decimal("3000"),
            "discount_rate": Decimal("5"),
            "low_value_exemption_elected": True
        }
        
        result = ifrs.validate_ifrs16_lease(lease)
        
        assert result.get("exemption") == "low_value"
    
    def test_invalid_lease_term(self):
        """Test lease with invalid term"""
        lease = {
            "lease_term_months": 0,
            "monthly_payment": Decimal("1000"),
            "underlying_asset_value": Decimal("10000"),
            "discount_rate": Decimal("5")
        }
        
        result = ifrs.validate_ifrs16_lease(lease)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "INVALID_LEASE_TERM"]
        assert len(violations) == 1


class TestFairValue:
    """Test IFRS 13 fair value measurement"""
    
    def test_level_1_quoted_price(self):
        """Test Level 1 fair value (quoted prices)"""
        asset = {"type": "stock"}
        market_data = {
            "quoted_price": 50.00,
            "market_active": True
        }
        
        result = ifrs.calculate_fair_value(asset, market_data)
        
        assert result["compliant"] is True
        assert result["fair_value"] == 50.0
        assert result["hierarchy_level"] == "Level 1"
    
    def test_level_2_comparable_prices(self):
        """Test Level 2 fair value (comparable prices)"""
        asset = {"type": "real_estate"}
        market_data = {
            "comparable_prices": [100000, 105000, 98000],
            "adjustments": {"location": 2000}
        }
        
        result = ifrs.calculate_fair_value(asset, market_data)
        
        assert result["compliant"] is True
        assert result["hierarchy_level"] == "Level 2"
        # Average of comparables: (100000 + 105000 + 98000) / 3 = 101000
        # Plus adjustment: 101000 + 2000 = 103000
        assert result["fair_value"] == 103000.0
    
    def test_level_3_cost_approach(self):
        """Test Level 3 fair value (cost approach)"""
        asset = {
            "replacement_cost": 100000,
            "accumulated_depreciation": 20000
        }
        market_data = {
            "valuation_method": "cost"
        }
        
        result = ifrs.calculate_fair_value(asset, market_data)
        
        assert result["compliant"] is True
        assert result["hierarchy_level"] == "Level 3"
        assert result["fair_value"] == 80000.0  # 100000 - 20000
    
    def test_level_3_income_approach(self):
        """Test Level 3 fair value (income approach)"""
        asset = {"type": "business"}
        market_data = {
            "valuation_method": "income",
            "future_cash_flows": [10000, 10000, 10000],
            "discount_rate": 10
        }
        
        result = ifrs.calculate_fair_value(asset, market_data)
        
        assert result["compliant"] is True
        assert result["hierarchy_level"] == "Level 3"
        assert result["fair_value"] > 0


class TestImpairment:
    """Test IAS 36 impairment of assets"""
    
    def test_no_impairment(self):
        """Test asset with no impairment"""
        asset = {
            "carrying_amount": 100000,
            "fair_value_less_costs_to_sell": 110000,
            "value_in_use": 105000
        }
        
        result = ifrs.validate_impairment(asset)
        
        assert result["impaired"] is False
        assert result["impairment_loss"] == 0.0
        assert result["recoverable_amount"] == 110000.0  # Higher of two
    
    def test_impairment_exists(self):
        """Test asset with impairment"""
        asset = {
            "carrying_amount": 100000,
            "fair_value_less_costs_to_sell": 80000,
            "value_in_use": 85000,
            "impairment_loss_recognized": 15000
        }
        
        result = ifrs.validate_impairment(asset)
        
        assert result["impaired"] is True
        assert result["impairment_loss"] == 15000.0  # 100000 - 85000
        assert result["recoverable_amount"] == 85000.0
        assert result["compliant"] is True  # Impairment was correctly recognized
    
    def test_impairment_not_recognized(self):
        """Test impairment exists but not recognized"""
        asset = {
            "carrying_amount": 100000,
            "fair_value_less_costs_to_sell": 70000,
            "value_in_use": 75000,
            "impairment_loss_recognized": 0  # Should have been 25000
        }
        
        result = ifrs.validate_impairment(asset)
        
        assert result["impaired"] is True
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "IMPAIRMENT_NOT_RECOGNIZED"]
        assert len(violations) == 1
    
    def test_incorrect_impairment_recognized(self):
        """Test impairment incorrectly recognized when not impaired"""
        asset = {
            "carrying_amount": 100000,
            "fair_value_less_costs_to_sell": 110000,
            "value_in_use": 105000,
            "impairment_loss_recognized": 5000  # Shouldn't recognize any
        }
        
        result = ifrs.validate_impairment(asset)
        
        assert result["impaired"] is False
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "INCORRECT_IMPAIRMENT"]
        assert len(violations) == 1
    
    def test_missing_recoverable_amount(self):
        """Test asset without recoverable amount"""
        asset = {
            "carrying_amount": 100000,
            "fair_value_less_costs_to_sell": 0,
            "value_in_use": 0
        }
        
        result = ifrs.validate_impairment(asset)
        
        assert result["compliant"] is False
        
        violations = [v for v in result["violations"] if v["type"] == "MISSING_RECOVERABLE_AMOUNT"]
        assert len(violations) == 1
