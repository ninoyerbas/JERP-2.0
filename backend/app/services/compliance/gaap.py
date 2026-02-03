"""
JERP 2.0 - GAAP Validation Engine
Implements US Generally Accepted Accounting Principles validation
"""
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, List


def validate_balance_sheet(assets: Dict[str, Decimal], liabilities: Dict[str, Decimal], equity: Dict[str, Decimal]) -> Dict[str, Any]:
    """
    Validate balance sheet equation: Assets = Liabilities + Equity
    
    Args:
        assets: Dict of asset accounts and amounts
        liabilities: Dict of liability accounts and amounts
        equity: Dict of equity accounts and amounts
        
    Returns:
        Dict with validation results and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "total_assets": Decimal("0"),
        "total_liabilities": Decimal("0"),
        "total_equity": Decimal("0"),
        "balance": Decimal("0")
    }
    
    # Calculate totals
    result["total_assets"] = sum(Decimal(str(v)) for v in assets.values())
    result["total_liabilities"] = sum(Decimal(str(v)) for v in liabilities.values())
    result["total_equity"] = sum(Decimal(str(v)) for v in equity.values())
    
    # Check balance sheet equation
    liabilities_plus_equity = result["total_liabilities"] + result["total_equity"]
    result["balance"] = result["total_assets"] - liabilities_plus_equity
    
    # Allow for small rounding differences (1 cent)
    if abs(result["balance"]) > Decimal("0.01"):
        result["compliant"] = False
        result["violations"].append({
            "type": "BALANCE_SHEET_IMBALANCE",
            "description": f"Assets ({result['total_assets']}) ≠ Liabilities ({result['total_liabilities']}) + Equity ({result['total_equity']}). Difference: {result['balance']}",
            "severity": "CRITICAL",
            "standard": "GAAP_FUNDAMENTAL_EQUATION"
        })
    
    # Validate asset classifications
    current_assets = Decimal("0")
    non_current_assets = Decimal("0")
    
    for account, amount in assets.items():
        account_lower = account.lower()
        if any(term in account_lower for term in ["cash", "receivable", "inventory", "prepaid", "current"]):
            current_assets += Decimal(str(amount))
        else:
            non_current_assets += Decimal(str(amount))
    
    # Validate liability classifications
    current_liabilities = Decimal("0")
    non_current_liabilities = Decimal("0")
    
    for account, amount in liabilities.items():
        account_lower = account.lower()
        if any(term in account_lower for term in ["payable", "current", "accrued", "short-term"]):
            current_liabilities += Decimal(str(amount))
        else:
            non_current_liabilities += Decimal(str(amount))
    
    result["current_assets"] = float(current_assets)
    result["non_current_assets"] = float(non_current_assets)
    result["current_liabilities"] = float(current_liabilities)
    result["non_current_liabilities"] = float(non_current_liabilities)
    
    # Convert to float for JSON
    result["total_assets"] = float(result["total_assets"])
    result["total_liabilities"] = float(result["total_liabilities"])
    result["total_equity"] = float(result["total_equity"])
    result["balance"] = float(result["balance"])
    
    return result


def validate_journal_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate journal entry according to GAAP double-entry bookkeeping rules.
    
    Requirements:
    - Debits must equal credits
    - Must have at least one debit and one credit
    - Account classifications must be valid
    - Dates must be reasonable
    
    Args:
        entry: Journal entry dict with debits, credits, date, description
        
    Returns:
        Dict with validation results and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "total_debits": Decimal("0"),
        "total_credits": Decimal("0"),
        "balance": Decimal("0")
    }
    
    debits = entry.get("debits", [])
    credits = entry.get("credits", [])
    entry_date = entry.get("date")
    description = entry.get("description", "")
    
    # Validate presence of debits and credits
    if not debits:
        result["compliant"] = False
        result["violations"].append({
            "type": "NO_DEBITS",
            "description": "Journal entry must have at least one debit",
            "severity": "CRITICAL",
            "standard": "GAAP_DOUBLE_ENTRY"
        })
    
    if not credits:
        result["compliant"] = False
        result["violations"].append({
            "type": "NO_CREDITS",
            "description": "Journal entry must have at least one credit",
            "severity": "CRITICAL",
            "standard": "GAAP_DOUBLE_ENTRY"
        })
    
    # Calculate totals
    for debit in debits:
        result["total_debits"] += Decimal(str(debit.get("amount", 0)))
    
    for credit in credits:
        result["total_credits"] += Decimal(str(credit.get("amount", 0)))
    
    # Validate debits = credits
    result["balance"] = result["total_debits"] - result["total_credits"]
    
    if abs(result["balance"]) > Decimal("0.01"):
        result["compliant"] = False
        result["violations"].append({
            "type": "UNBALANCED_ENTRY",
            "description": f"Debits ({result['total_debits']}) ≠ Credits ({result['total_credits']}). Difference: {result['balance']}",
            "severity": "CRITICAL",
            "standard": "GAAP_DOUBLE_ENTRY"
        })
    
    # Validate date
    if entry_date:
        try:
            entry_datetime = datetime.fromisoformat(entry_date) if isinstance(entry_date, str) else entry_date
            
            # Check if date is in the future
            if entry_datetime > datetime.now():
                result["violations"].append({
                    "type": "FUTURE_DATE",
                    "description": "Journal entry date is in the future",
                    "severity": "HIGH",
                    "standard": "GAAP_PERIOD_CUTOFF"
                })
                result["compliant"] = False
        except (ValueError, TypeError):
            result["violations"].append({
                "type": "INVALID_DATE",
                "description": "Invalid date format",
                "severity": "HIGH",
                "standard": "GAAP_RECORDKEEPING"
            })
            result["compliant"] = False
    else:
        result["violations"].append({
            "type": "MISSING_DATE",
            "description": "Journal entry must have a date",
            "severity": "HIGH",
            "standard": "GAAP_RECORDKEEPING"
        })
        result["compliant"] = False
    
    # Validate description
    if not description or len(description.strip()) < 5:
        result["violations"].append({
            "type": "INSUFFICIENT_DESCRIPTION",
            "description": "Journal entry must have meaningful description",
            "severity": "MEDIUM",
            "standard": "GAAP_RECORDKEEPING"
        })
    
    # Convert to float for JSON
    result["total_debits"] = float(result["total_debits"])
    result["total_credits"] = float(result["total_credits"])
    result["balance"] = float(result["balance"])
    
    return result


def validate_revenue_recognition(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate revenue recognition according to ASC 606 (GAAP).
    
    Five-step model:
    1. Identify the contract with customer
    2. Identify performance obligations
    3. Determine transaction price
    4. Allocate transaction price to performance obligations
    5. Recognize revenue when (or as) performance obligation is satisfied
    
    Args:
        transaction: Transaction dict with contract details
        
    Returns:
        Dict with validation results and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "revenue_recognizable": Decimal("0")
    }
    
    # Step 1: Validate contract exists
    if not transaction.get("contract_id"):
        result["compliant"] = False
        result["violations"].append({
            "type": "NO_CONTRACT",
            "description": "Revenue recognition requires identified contract",
            "severity": "CRITICAL",
            "standard": "GAAP_ASC_606_STEP_1"
        })
    
    # Step 2: Validate performance obligations identified
    performance_obligations = transaction.get("performance_obligations", [])
    if not performance_obligations:
        result["compliant"] = False
        result["violations"].append({
            "type": "NO_PERFORMANCE_OBLIGATIONS",
            "description": "Must identify distinct performance obligations",
            "severity": "CRITICAL",
            "standard": "GAAP_ASC_606_STEP_2"
        })
    
    # Step 3: Validate transaction price
    transaction_price = transaction.get("transaction_price")
    if not transaction_price or Decimal(str(transaction_price)) <= 0:
        result["compliant"] = False
        result["violations"].append({
            "type": "INVALID_TRANSACTION_PRICE",
            "description": "Transaction price must be determinable and positive",
            "severity": "CRITICAL",
            "standard": "GAAP_ASC_606_STEP_3"
        })
    
    # Step 4 & 5: Calculate recognizable revenue based on satisfied obligations
    total_allocated = Decimal("0")
    
    for obligation in performance_obligations:
        allocated_price = Decimal(str(obligation.get("allocated_price", 0)))
        is_satisfied = obligation.get("is_satisfied", False)
        satisfaction_date = obligation.get("satisfaction_date")
        
        if is_satisfied:
            # Validate satisfaction date is not in future
            if satisfaction_date:
                try:
                    sat_date = datetime.fromisoformat(satisfaction_date) if isinstance(satisfaction_date, str) else satisfaction_date
                    if sat_date > datetime.now():
                        result["violations"].append({
                            "type": "FUTURE_SATISFACTION_DATE",
                            "description": f"Performance obligation satisfied in future: {satisfaction_date}",
                            "severity": "HIGH",
                            "standard": "GAAP_ASC_606_STEP_5"
                        })
                        result["compliant"] = False
                        continue
                except (ValueError, TypeError):
                    pass
            
            result["revenue_recognizable"] += allocated_price
        
        total_allocated += allocated_price
    
    # Validate allocation equals transaction price
    if transaction_price and abs(total_allocated - Decimal(str(transaction_price))) > Decimal("0.01"):
        result["violations"].append({
            "type": "ALLOCATION_MISMATCH",
            "description": f"Allocated amounts ({total_allocated}) don't match transaction price ({transaction_price})",
            "severity": "HIGH",
            "standard": "GAAP_ASC_606_STEP_4"
        })
        result["compliant"] = False
    
    result["revenue_recognizable"] = float(result["revenue_recognizable"])
    
    return result


def validate_depreciation(asset: Dict[str, Any], method: str) -> Dict[str, Any]:
    """
    Validate depreciation calculation according to GAAP.
    
    Common methods:
    - Straight-line
    - Double declining balance
    - Units of production
    
    Args:
        asset: Asset dict with cost, salvage_value, useful_life, accumulated_depreciation
        method: Depreciation method
        
    Returns:
        Dict with validation results and violations
    """
    result = {
        "compliant": True,
        "violations": [],
        "annual_depreciation": Decimal("0"),
        "depreciation_expense": Decimal("0")
    }
    
    cost = Decimal(str(asset.get("cost", 0)))
    salvage_value = Decimal(str(asset.get("salvage_value", 0)))
    useful_life = asset.get("useful_life_years", 0)
    accumulated_depreciation = Decimal(str(asset.get("accumulated_depreciation", 0)))
    
    # Validate required fields
    if cost <= 0:
        result["compliant"] = False
        result["violations"].append({
            "type": "INVALID_COST",
            "description": "Asset cost must be positive",
            "severity": "CRITICAL",
            "standard": "GAAP_DEPRECIATION"
        })
        return result
    
    if useful_life <= 0:
        result["compliant"] = False
        result["violations"].append({
            "type": "INVALID_USEFUL_LIFE",
            "description": "Useful life must be positive",
            "severity": "CRITICAL",
            "standard": "GAAP_DEPRECIATION"
        })
        return result
    
    if salvage_value < 0:
        result["violations"].append({
            "type": "NEGATIVE_SALVAGE_VALUE",
            "description": "Salvage value should not be negative",
            "severity": "MEDIUM",
            "standard": "GAAP_DEPRECIATION"
        })
    
    if salvage_value >= cost:
        result["violations"].append({
            "type": "SALVAGE_EXCEEDS_COST",
            "description": "Salvage value should not exceed cost",
            "severity": "HIGH",
            "standard": "GAAP_DEPRECIATION"
        })
        result["compliant"] = False
    
    # Calculate depreciation based on method
    depreciable_base = cost - salvage_value
    
    if method.lower() == "straight-line":
        result["annual_depreciation"] = depreciable_base / Decimal(str(useful_life))
    elif method.lower() in ["double-declining", "double declining balance", "ddb"]:
        rate = Decimal("2") / Decimal(str(useful_life))
        book_value = cost - accumulated_depreciation
        result["annual_depreciation"] = book_value * rate
        
        # Ensure doesn't depreciate below salvage value
        if cost - accumulated_depreciation - result["annual_depreciation"] < salvage_value:
            result["annual_depreciation"] = max(Decimal("0"), book_value - salvage_value)
    else:
        result["violations"].append({
            "type": "UNSUPPORTED_METHOD",
            "description": f"Depreciation method '{method}' not recognized",
            "severity": "HIGH",
            "standard": "GAAP_DEPRECIATION"
        })
        result["compliant"] = False
    
    # Validate accumulated depreciation doesn't exceed depreciable base
    if accumulated_depreciation > depreciable_base:
        result["violations"].append({
            "type": "OVER_DEPRECIATION",
            "description": "Accumulated depreciation exceeds depreciable base",
            "severity": "CRITICAL",
            "standard": "GAAP_DEPRECIATION"
        })
        result["compliant"] = False
    
    result["depreciation_expense"] = result["annual_depreciation"]
    result["annual_depreciation"] = float(result["annual_depreciation"])
    result["depreciation_expense"] = float(result["depreciation_expense"])
    result["depreciable_base"] = float(depreciable_base)
    
    return result
