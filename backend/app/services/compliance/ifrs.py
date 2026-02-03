"""
JERP 2.0 - IFRS Validation Engine
Implements International Financial Reporting Standards validation
"""
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, List


def validate_ifrs15_revenue(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate revenue recognition according to IFRS 15 (Revenue from Contracts with Customers).
    
    Five-step model (similar to GAAP ASC 606):
    1. Identify the contract
    2. Identify performance obligations
    3. Determine transaction price
    4. Allocate transaction price
    5. Recognize revenue when obligations satisfied
    
    Args:
        contract: Contract dict with customer, obligations, pricing
        
    Returns:
        Dict with validation results and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "revenue_recognizable": Decimal("0")
    }
    
    # Step 1: Identify contract
    if not contract.get("customer_id"):
        result["compliant"] = False
        result["violations"].append({
            "type": "NO_CUSTOMER",
            "description": "Contract must identify customer",
            "severity": "CRITICAL",
            "standard": "IFRS_15_IDENTIFICATION"
        })
    
    # Validate contract has commercial substance
    if not contract.get("has_commercial_substance", True):
        result["violations"].append({
            "type": "NO_COMMERCIAL_SUBSTANCE",
            "description": "Contract lacks commercial substance",
            "severity": "CRITICAL",
            "standard": "IFRS_15_CONTRACT_CRITERIA"
        })
        result["compliant"] = False
    
    # Validate payment terms are probable
    if not contract.get("payment_probable", True):
        result["violations"].append({
            "type": "PAYMENT_NOT_PROBABLE",
            "description": "Collection of consideration not probable",
            "severity": "HIGH",
            "standard": "IFRS_15_CONTRACT_CRITERIA"
        })
        result["compliant"] = False
    
    # Step 2: Performance obligations
    performance_obligations = contract.get("performance_obligations", [])
    if not performance_obligations:
        result["compliant"] = False
        result["violations"].append({
            "type": "NO_PERFORMANCE_OBLIGATIONS",
            "description": "Must identify distinct performance obligations",
            "severity": "CRITICAL",
            "standard": "IFRS_15_PERFORMANCE_OBLIGATIONS"
        })
    
    # Step 3: Transaction price
    transaction_price = contract.get("transaction_price")
    if not transaction_price or Decimal(str(transaction_price)) <= 0:
        result["compliant"] = False
        result["violations"].append({
            "type": "INVALID_TRANSACTION_PRICE",
            "description": "Transaction price must be determinable",
            "severity": "CRITICAL",
            "standard": "IFRS_15_TRANSACTION_PRICE"
        })
    
    # Check for variable consideration
    variable_consideration = contract.get("variable_consideration", {})
    if variable_consideration:
        constraint_applied = variable_consideration.get("constraint_applied", False)
        if not constraint_applied:
            result["violations"].append({
                "type": "VARIABLE_CONSIDERATION_CONSTRAINT",
                "description": "Variable consideration must be constrained to probable amounts",
                "severity": "HIGH",
                "standard": "IFRS_15_VARIABLE_CONSIDERATION"
            })
    
    # Step 4 & 5: Allocation and recognition
    total_allocated = Decimal("0")
    
    for obligation in performance_obligations:
        allocated_price = Decimal(str(obligation.get("allocated_price", 0)))
        satisfaction_method = obligation.get("satisfaction_method", "point_in_time")
        progress = obligation.get("progress_percentage", 0)
        
        # Validate satisfaction method
        if satisfaction_method not in ["point_in_time", "over_time"]:
            result["violations"].append({
                "type": "INVALID_SATISFACTION_METHOD",
                "description": f"Invalid satisfaction method: {satisfaction_method}",
                "severity": "HIGH",
                "standard": "IFRS_15_SATISFACTION"
            })
            result["compliant"] = False
        
        # Calculate recognizable revenue
        if satisfaction_method == "over_time":
            # Revenue recognized based on progress
            if progress < 0 or progress > 100:
                result["violations"].append({
                    "type": "INVALID_PROGRESS",
                    "description": f"Progress percentage must be 0-100: {progress}",
                    "severity": "HIGH",
                    "standard": "IFRS_15_PROGRESS_MEASUREMENT"
                })
                result["compliant"] = False
            else:
                result["revenue_recognizable"] += allocated_price * Decimal(str(progress)) / Decimal("100")
        else:
            # Point in time - recognize when control transfers
            control_transferred = obligation.get("control_transferred", False)
            if control_transferred:
                result["revenue_recognizable"] += allocated_price
        
        total_allocated += allocated_price
    
    # Validate allocation
    if transaction_price and abs(total_allocated - Decimal(str(transaction_price))) > Decimal("0.01"):
        result["violations"].append({
            "type": "ALLOCATION_MISMATCH",
            "description": f"Allocated amounts don't match transaction price",
            "severity": "HIGH",
            "standard": "IFRS_15_ALLOCATION"
        })
        result["compliant"] = False
    
    result["revenue_recognizable"] = float(result["revenue_recognizable"])
    
    return result


def validate_ifrs16_lease(lease: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate lease accounting according to IFRS 16 (Leases).
    
    Key requirements:
    - Recognition of right-of-use asset and lease liability
    - Measurement at present value of lease payments
    - Exemptions for short-term and low-value leases
    
    Args:
        lease: Lease dict with terms, payments, classification
        
    Returns:
        Dict with validation results and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "right_of_use_asset": Decimal("0"),
        "lease_liability": Decimal("0")
    }
    
    lease_term_months = lease.get("lease_term_months", 0)
    monthly_payment = Decimal(str(lease.get("monthly_payment", 0)))
    asset_value = Decimal(str(lease.get("underlying_asset_value", 0)))
    discount_rate = Decimal(str(lease.get("discount_rate", 0)))
    
    # Check for exemptions
    is_short_term = lease_term_months <= 12
    is_low_value = asset_value <= Decimal("5000")  # Simplified threshold
    
    if is_short_term and lease.get("short_term_exemption_elected"):
        result["exemption"] = "short_term"
        result["note"] = "Short-term lease exemption applied"
        return result
    
    if is_low_value and lease.get("low_value_exemption_elected"):
        result["exemption"] = "low_value"
        result["note"] = "Low-value asset exemption applied"
        return result
    
    # Validate required fields for lease recognition
    if lease_term_months <= 0:
        result["compliant"] = False
        result["violations"].append({
            "type": "INVALID_LEASE_TERM",
            "description": "Lease term must be positive",
            "severity": "CRITICAL",
            "standard": "IFRS_16_RECOGNITION"
        })
    
    if monthly_payment <= 0:
        result["compliant"] = False
        result["violations"].append({
            "type": "INVALID_PAYMENT",
            "description": "Lease payment must be positive",
            "severity": "CRITICAL",
            "standard": "IFRS_16_MEASUREMENT"
        })
    
    if discount_rate <= 0:
        result["violations"].append({
            "type": "MISSING_DISCOUNT_RATE",
            "description": "Discount rate required for present value calculation",
            "severity": "HIGH",
            "standard": "IFRS_16_MEASUREMENT"
        })
        result["compliant"] = False
    
    # Calculate present value of lease payments (simplified)
    if discount_rate > 0 and monthly_payment > 0 and lease_term_months > 0:
        monthly_rate = discount_rate / Decimal("12") / Decimal("100")
        
        # Present value of annuity formula
        if monthly_rate > 0:
            pv_factor = (Decimal("1") - (Decimal("1") + monthly_rate) ** -lease_term_months) / monthly_rate
            result["lease_liability"] = monthly_payment * pv_factor
        else:
            result["lease_liability"] = monthly_payment * Decimal(str(lease_term_months))
        
        # Right-of-use asset = lease liability + initial direct costs + prepayments - incentives
        initial_direct_costs = Decimal(str(lease.get("initial_direct_costs", 0)))
        prepayments = Decimal(str(lease.get("prepayments", 0)))
        lease_incentives = Decimal(str(lease.get("lease_incentives", 0)))
        
        result["right_of_use_asset"] = result["lease_liability"] + initial_direct_costs + prepayments - lease_incentives
    
    # Validate that both asset and liability are recognized
    if result["lease_liability"] == 0:
        result["violations"].append({
            "type": "NO_LIABILITY_RECOGNIZED",
            "description": "Lease liability must be recognized",
            "severity": "CRITICAL",
            "standard": "IFRS_16_RECOGNITION"
        })
        result["compliant"] = False
    
    if result["right_of_use_asset"] == 0:
        result["violations"].append({
            "type": "NO_ASSET_RECOGNIZED",
            "description": "Right-of-use asset must be recognized",
            "severity": "CRITICAL",
            "standard": "IFRS_16_RECOGNITION"
        })
        result["compliant"] = False
    
    result["right_of_use_asset"] = float(result["right_of_use_asset"])
    result["lease_liability"] = float(result["lease_liability"])
    
    return result


def calculate_fair_value(asset: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate fair value according to IFRS 13 (Fair Value Measurement).
    
    Fair value hierarchy:
    - Level 1: Quoted prices in active markets
    - Level 2: Observable inputs other than quoted prices
    - Level 3: Unobservable inputs
    
    Args:
        asset: Asset dict with characteristics
        market_data: Market data dict with pricing information
        
    Returns:
        Dict with fair value and hierarchy level
    """
    result = {
        "fair_value": Decimal("0"),
        "hierarchy_level": None,
        "compliant": True,
        "violations": [],
        "valuation_technique": None
    }
    
    # Level 1: Quoted prices in active markets
    if market_data.get("quoted_price") and market_data.get("market_active"):
        result["fair_value"] = Decimal(str(market_data["quoted_price"]))
        result["hierarchy_level"] = "Level 1"
        result["valuation_technique"] = "market_approach"
        result["note"] = "Most reliable fair value measurement"
    
    # Level 2: Observable market inputs
    elif market_data.get("comparable_prices"):
        comparable_prices = [Decimal(str(p)) for p in market_data["comparable_prices"]]
        if comparable_prices:
            # Use average of comparable prices
            result["fair_value"] = sum(comparable_prices) / Decimal(str(len(comparable_prices)))
            result["hierarchy_level"] = "Level 2"
            result["valuation_technique"] = "market_approach"
            
            # Apply adjustments for differences
            adjustments = market_data.get("adjustments", {})
            for adj_name, adj_value in adjustments.items():
                result["fair_value"] += Decimal(str(adj_value))
    
    # Level 3: Unobservable inputs (use cost or income approach)
    else:
        valuation_method = market_data.get("valuation_method", "cost")
        
        if valuation_method == "cost":
            # Cost approach
            replacement_cost = Decimal(str(asset.get("replacement_cost", 0)))
            accumulated_depreciation = Decimal(str(asset.get("accumulated_depreciation", 0)))
            result["fair_value"] = replacement_cost - accumulated_depreciation
            result["valuation_technique"] = "cost_approach"
        elif valuation_method == "income":
            # Income approach (discounted cash flows)
            future_cash_flows = [Decimal(str(cf)) for cf in market_data.get("future_cash_flows", [])]
            discount_rate = Decimal(str(market_data.get("discount_rate", 10))) / Decimal("100")
            
            present_value = Decimal("0")
            for i, cash_flow in enumerate(future_cash_flows, start=1):
                present_value += cash_flow / ((Decimal("1") + discount_rate) ** i)
            
            result["fair_value"] = present_value
            result["valuation_technique"] = "income_approach"
        else:
            result["violations"].append({
                "type": "INVALID_VALUATION_METHOD",
                "description": f"Valuation method '{valuation_method}' not recognized",
                "severity": "HIGH",
                "standard": "IFRS_13_VALUATION"
            })
            result["compliant"] = False
        
        result["hierarchy_level"] = "Level 3"
        result["note"] = "Least reliable fair value measurement - requires disclosure"
    
    # Validate fair value is reasonable
    if result["fair_value"] < 0:
        result["violations"].append({
            "type": "NEGATIVE_FAIR_VALUE",
            "description": "Fair value cannot be negative for most assets",
            "severity": "HIGH",
            "standard": "IFRS_13_MEASUREMENT"
        })
        result["compliant"] = False
    
    result["fair_value"] = float(result["fair_value"])
    
    return result


def validate_impairment(asset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate asset impairment according to IAS 36 (Impairment of Assets).
    
    Key concepts:
    - Recoverable amount = higher of fair value less costs to sell and value in use
    - Impairment loss = carrying amount - recoverable amount
    
    Args:
        asset: Asset dict with carrying amount and recoverable amount
        
    Returns:
        Dict with impairment assessment and violations
    """
    result = {
        "impaired": False,
        "impairment_loss": Decimal("0"),
        "compliant": True,
        "violations": []
    }
    
    carrying_amount = Decimal(str(asset.get("carrying_amount", 0)))
    fair_value_less_costs = Decimal(str(asset.get("fair_value_less_costs_to_sell", 0)))
    value_in_use = Decimal(str(asset.get("value_in_use", 0)))
    
    # Check for impairment indicators
    indicators = asset.get("impairment_indicators", [])
    if indicators:
        result["impairment_indicators"] = indicators
        result["note"] = "Impairment test required due to indicators present"
    
    # Validate required amounts
    if carrying_amount <= 0:
        result["violations"].append({
            "type": "INVALID_CARRYING_AMOUNT",
            "description": "Carrying amount must be positive",
            "severity": "HIGH",
            "standard": "IAS_36_MEASUREMENT"
        })
        result["compliant"] = False
        return result
    
    # Calculate recoverable amount
    if fair_value_less_costs == 0 and value_in_use == 0:
        result["violations"].append({
            "type": "MISSING_RECOVERABLE_AMOUNT",
            "description": "Either fair value less costs or value in use must be determined",
            "severity": "CRITICAL",
            "standard": "IAS_36_RECOVERABLE_AMOUNT"
        })
        result["compliant"] = False
        return result
    
    # Recoverable amount is the higher of the two
    recoverable_amount = max(fair_value_less_costs, value_in_use)
    result["recoverable_amount"] = float(recoverable_amount)
    
    # Check for impairment
    if carrying_amount > recoverable_amount:
        result["impaired"] = True
        result["impairment_loss"] = carrying_amount - recoverable_amount
        
        # Validate that impairment loss was recognized
        impairment_recognized = Decimal(str(asset.get("impairment_loss_recognized", 0)))
        
        if abs(impairment_recognized - result["impairment_loss"]) > Decimal("0.01"):
            result["violations"].append({
                "type": "IMPAIRMENT_NOT_RECOGNIZED",
                "description": f"Impairment loss of {result['impairment_loss']} should be recognized",
                "severity": "CRITICAL",
                "standard": "IAS_36_RECOGNITION"
            })
            result["compliant"] = False
    else:
        result["note"] = "No impairment - carrying amount does not exceed recoverable amount"
        
        # Check if impairment loss was incorrectly recognized
        impairment_recognized = Decimal(str(asset.get("impairment_loss_recognized", 0)))
        if impairment_recognized > 0:
            result["violations"].append({
                "type": "INCORRECT_IMPAIRMENT",
                "description": "Impairment loss recognized when asset is not impaired",
                "severity": "HIGH",
                "standard": "IAS_36_RECOGNITION"
            })
            result["compliant"] = False
    
    result["impairment_loss"] = float(result["impairment_loss"])
    result["carrying_amount"] = float(carrying_amount)
    
    return result
