"""
JERP 2.0 - GAAP (Generally Accepted Accounting Principles) Validation Engine
Implements US GAAP compliance checks for financial transactions and statements
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class InventoryMethod(str, Enum):
    """Inventory valuation methods allowed under GAAP"""
    FIFO = "FIFO"  # First In, First Out
    LIFO = "LIFO"  # Last In, First Out
    AVERAGE_COST = "AVERAGE_COST"  # Weighted Average
    SPECIFIC_IDENTIFICATION = "SPECIFIC_IDENTIFICATION"


class DepreciationMethod(str, Enum):
    """Depreciation methods allowed under GAAP"""
    STRAIGHT_LINE = "STRAIGHT_LINE"
    DECLINING_BALANCE = "DECLINING_BALANCE"
    DOUBLE_DECLINING = "DOUBLE_DECLINING"
    UNITS_OF_PRODUCTION = "UNITS_OF_PRODUCTION"
    SUM_OF_YEARS_DIGITS = "SUM_OF_YEARS_DIGITS"


class AssetClassification(str, Enum):
    """Asset classification types"""
    CURRENT = "CURRENT"  # Expected to be converted to cash within 1 year
    NON_CURRENT = "NON_CURRENT"  # Long-term assets


class LiabilityClassification(str, Enum):
    """Liability classification types"""
    CURRENT = "CURRENT"  # Due within 1 year
    NON_CURRENT = "NON_CURRENT"  # Due after 1 year


@dataclass
class GAAPViolation:
    """Represents a GAAP compliance violation"""
    principle: str
    description: str
    severity: str
    affected_account: Optional[str] = None
    amount: Optional[Decimal] = None


@dataclass
class BalanceSheetValidation:
    """Result of balance sheet validation"""
    is_balanced: bool
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    discrepancy: Decimal
    violations: List[GAAPViolation]


class GAAP:
    """
    Generally Accepted Accounting Principles (GAAP) validation engine.
    
    Core principles implemented:
    - Revenue Recognition
    - Matching Principle
    - Full Disclosure
    - Consistency
    - Materiality
    - Going Concern
    - Accrual Basis
    """
    
    # Materiality threshold (as percentage of total assets/revenue)
    MATERIALITY_THRESHOLD_PCT = Decimal("0.05")  # 5%
    
    # Asset useful life ranges (in years)
    BUILDING_MIN_LIFE = 20
    BUILDING_MAX_LIFE = 40
    EQUIPMENT_MIN_LIFE = 3
    EQUIPMENT_MAX_LIFE = 20
    VEHICLE_MIN_LIFE = 3
    VEHICLE_MAX_LIFE = 10
    
    def __init__(self):
        """Initialize GAAP validation engine"""
        pass
    
    def validate_balance_sheet(
        self,
        assets: Dict[str, Decimal],
        liabilities: Dict[str, Decimal],
        equity: Dict[str, Decimal]
    ) -> BalanceSheetValidation:
        """
        Validate balance sheet equation: Assets = Liabilities + Equity
        
        Args:
            assets: Dictionary of asset accounts and amounts
            liabilities: Dictionary of liability accounts and amounts
            equity: Dictionary of equity accounts and amounts
            
        Returns:
            BalanceSheetValidation with results
        """
        violations = []
        
        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        total_equity = sum(equity.values())
        
        liabilities_plus_equity = total_liabilities + total_equity
        discrepancy = total_assets - liabilities_plus_equity
        
        is_balanced = abs(discrepancy) < Decimal("0.01")  # Allow for rounding
        
        if not is_balanced:
            violations.append(GAAPViolation(
                principle="Balance Sheet Equation",
                description=f"Assets (${total_assets}) != Liabilities (${total_liabilities}) + Equity (${total_equity}). Discrepancy: ${discrepancy}",
                severity="CRITICAL",
                amount=discrepancy
            ))
        
        return BalanceSheetValidation(
            is_balanced=is_balanced,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            discrepancy=discrepancy,
            violations=violations
        )
    
    def validate_revenue_recognition(
        self,
        revenue_amount: Decimal,
        service_delivered: bool,
        goods_delivered: bool,
        payment_received: bool,
        revenue_recognition_date: date,
        transaction_date: date
    ) -> List[GAAPViolation]:
        """
        Validate revenue recognition under GAAP principles.
        
        Revenue should be recognized when:
        1. It is earned (goods/services delivered)
        2. It is realizable (payment received or reasonably assured)
        
        Args:
            revenue_amount: Amount of revenue
            service_delivered: Whether service has been delivered
            goods_delivered: Whether goods have been delivered
            payment_received: Whether payment has been received
            revenue_recognition_date: Date revenue was recognized
            transaction_date: Date of original transaction
            
        Returns:
            List of GAAPViolation objects
        """
        violations = []
        
        # Check if revenue was earned
        if not (service_delivered or goods_delivered):
            violations.append(GAAPViolation(
                principle="Revenue Recognition - Earned",
                description=f"Revenue of ${revenue_amount} recognized before goods/services delivered",
                severity="HIGH",
                amount=revenue_amount
            ))
        
        # Check timing
        if revenue_recognition_date < transaction_date:
            violations.append(GAAPViolation(
                principle="Revenue Recognition - Timing",
                description=f"Revenue recognized before transaction date",
                severity="HIGH",
                amount=revenue_amount
            ))
        
        # For accrual accounting, payment doesn't need to be received
        # But recognition should align with delivery
        
        return violations
    
    def validate_matching_principle(
        self,
        expense_amount: Decimal,
        related_revenue_amount: Decimal,
        expense_period: str,
        revenue_period: str,
        expense_description: str
    ) -> List[GAAPViolation]:
        """
        Validate matching principle: expenses should be matched with related revenues.
        
        Args:
            expense_amount: Amount of expense
            related_revenue_amount: Amount of related revenue
            expense_period: Period when expense was recorded (e.g., "2024-01")
            revenue_period: Period when related revenue was recorded
            expense_description: Description of expense
            
        Returns:
            List of GAAPViolation objects
        """
        violations = []
        
        if expense_period != revenue_period:
            violations.append(GAAPViolation(
                principle="Matching Principle",
                description=f"Expense '{expense_description}' (${expense_amount}) in period {expense_period} does not match related revenue (${related_revenue_amount}) in period {revenue_period}",
                severity="MEDIUM",
                amount=expense_amount
            ))
        
        return violations
    
    def validate_inventory_valuation(
        self,
        method: InventoryMethod,
        beginning_inventory: Decimal,
        purchases: Decimal,
        ending_inventory: Decimal,
        cost_of_goods_sold: Decimal
    ) -> List[GAAPViolation]:
        """
        Validate inventory valuation and COGS calculation.
        
        Formula: Beginning Inventory + Purchases - Ending Inventory = COGS
        
        Args:
            method: Inventory valuation method
            beginning_inventory: Beginning inventory value
            purchases: Total purchases during period
            ending_inventory: Ending inventory value
            cost_of_goods_sold: Calculated COGS
            
        Returns:
            List of GAAPViolation objects
        """
        violations = []
        
        # Validate COGS calculation
        calculated_cogs = beginning_inventory + purchases - ending_inventory
        cogs_difference = abs(calculated_cogs - cost_of_goods_sold)
        
        if cogs_difference > Decimal("0.01"):
            violations.append(GAAPViolation(
                principle="Inventory Valuation",
                description=f"COGS calculation error. Expected: ${calculated_cogs}, Recorded: ${cost_of_goods_sold}, Difference: ${cogs_difference}",
                severity="HIGH",
                affected_account="Cost of Goods Sold",
                amount=cogs_difference
            ))
        
        # Validate that inventory values are non-negative
        if ending_inventory < Decimal("0"):
            violations.append(GAAPViolation(
                principle="Inventory Valuation",
                description=f"Negative ending inventory: ${ending_inventory}",
                severity="CRITICAL",
                affected_account="Inventory",
                amount=ending_inventory
            ))
        
        return violations
    
    def validate_depreciation(
        self,
        asset_cost: Decimal,
        salvage_value: Decimal,
        useful_life_years: int,
        method: DepreciationMethod,
        accumulated_depreciation: Decimal,
        years_elapsed: int
    ) -> List[GAAPViolation]:
        """
        Validate depreciation calculation.
        
        Args:
            asset_cost: Original cost of asset
            salvage_value: Expected salvage value
            useful_life_years: Estimated useful life
            method: Depreciation method used
            accumulated_depreciation: Total depreciation to date
            years_elapsed: Years since acquisition
            
        Returns:
            List of GAAPViolation objects
        """
        violations = []
        
        # Validate useful life is reasonable
        if useful_life_years < 1:
            violations.append(GAAPViolation(
                principle="Depreciation",
                description=f"Useful life of {useful_life_years} years is invalid",
                severity="HIGH",
                amount=asset_cost
            ))
            return violations
        
        # Calculate expected depreciation for straight-line method
        if method == DepreciationMethod.STRAIGHT_LINE:
            depreciable_amount = asset_cost - salvage_value
            annual_depreciation = depreciable_amount / useful_life_years
            expected_accumulated = min(annual_depreciation * years_elapsed, depreciable_amount)
            
            difference = abs(accumulated_depreciation - expected_accumulated)
            tolerance = expected_accumulated * Decimal("0.01")  # 1% tolerance
            
            if difference > tolerance:
                violations.append(GAAPViolation(
                    principle="Depreciation - Straight Line",
                    description=f"Accumulated depreciation ${accumulated_depreciation} differs from expected ${expected_accumulated}",
                    severity="MEDIUM",
                    amount=difference
                ))
        
        # Validate accumulated depreciation doesn't exceed depreciable amount
        max_depreciation = asset_cost - salvage_value
        if accumulated_depreciation > max_depreciation:
            violations.append(GAAPViolation(
                principle="Depreciation",
                description=f"Accumulated depreciation ${accumulated_depreciation} exceeds maximum ${max_depreciation}",
                severity="HIGH",
                amount=accumulated_depreciation - max_depreciation
            ))
        
        return violations
    
    def validate_asset_classification(
        self,
        asset_name: str,
        classification: AssetClassification,
        expected_conversion_date: Optional[date],
        acquisition_date: date
    ) -> List[GAAPViolation]:
        """
        Validate proper classification of assets (current vs. non-current).
        
        Current assets: Expected to be converted to cash within 1 year
        Non-current assets: Long-term assets
        
        Args:
            asset_name: Name of the asset
            classification: Current or Non-current
            expected_conversion_date: When asset expected to convert to cash
            acquisition_date: When asset was acquired
            
        Returns:
            List of GAAPViolation objects
        """
        violations = []
        
        if expected_conversion_date:
            days_to_conversion = (expected_conversion_date - acquisition_date).days
            
            if classification == AssetClassification.CURRENT and days_to_conversion > 365:
                violations.append(GAAPViolation(
                    principle="Asset Classification",
                    description=f"Asset '{asset_name}' classified as current but conversion expected in {days_to_conversion} days (>1 year)",
                    severity="MEDIUM",
                    affected_account=asset_name
                ))
            
            if classification == AssetClassification.NON_CURRENT and days_to_conversion <= 365:
                violations.append(GAAPViolation(
                    principle="Asset Classification",
                    description=f"Asset '{asset_name}' classified as non-current but conversion expected in {days_to_conversion} days (<=1 year)",
                    severity="MEDIUM",
                    affected_account=asset_name
                ))
        
        return violations
    
    def validate_materiality(
        self,
        transaction_amount: Decimal,
        total_assets: Decimal,
        total_revenue: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Assess if a transaction is material (significant enough to affect decisions).
        
        Rule of thumb: Transaction is material if > 5% of total assets or revenue
        
        Args:
            transaction_amount: Amount of transaction
            total_assets: Total assets of company
            total_revenue: Total revenue of company
            
        Returns:
            Tuple of (is_material, explanation)
        """
        asset_threshold = total_assets * self.MATERIALITY_THRESHOLD_PCT
        revenue_threshold = total_revenue * self.MATERIALITY_THRESHOLD_PCT
        
        is_material = (
            transaction_amount >= asset_threshold or
            transaction_amount >= revenue_threshold
        )
        
        explanation = None
        if is_material:
            explanation = f"Transaction of ${transaction_amount} exceeds materiality threshold (${min(asset_threshold, revenue_threshold)})"
        
        return is_material, explanation
    
    def validate_going_concern(
        self,
        current_assets: Decimal,
        current_liabilities: Decimal,
        net_income_last_period: Decimal,
        cash_flow_from_operations: Decimal
    ) -> List[GAAPViolation]:
        """
        Assess going concern (ability to continue operations).
        
        Warning signs:
        - Current ratio < 1 (can't pay short-term debts)
        - Negative net income
        - Negative operating cash flow
        
        Args:
            current_assets: Total current assets
            current_liabilities: Total current liabilities
            net_income_last_period: Net income from last period
            cash_flow_from_operations: Cash flow from operations
            
        Returns:
            List of GAAPViolation objects (warnings)
        """
        violations = []
        
        # Current ratio check
        if current_liabilities > Decimal("0"):
            current_ratio = current_assets / current_liabilities
            if current_ratio < Decimal("1.0"):
                violations.append(GAAPViolation(
                    principle="Going Concern",
                    description=f"Current ratio {current_ratio:.2f} is below 1.0, indicating potential liquidity issues",
                    severity="HIGH",
                    amount=current_liabilities - current_assets
                ))
        
        # Net income check
        if net_income_last_period < Decimal("0"):
            violations.append(GAAPViolation(
                principle="Going Concern",
                description=f"Negative net income of ${net_income_last_period} indicates profitability concerns",
                severity="MEDIUM",
                amount=net_income_last_period
            ))
        
        # Operating cash flow check
        if cash_flow_from_operations < Decimal("0"):
            violations.append(GAAPViolation(
                principle="Going Concern",
                description=f"Negative operating cash flow of ${cash_flow_from_operations} indicates cash concerns",
                severity="HIGH",
                amount=cash_flow_from_operations
            ))
        
        return violations
    
    def validate_consistency(
        self,
        current_method: str,
        previous_method: str,
        account_type: str,
        change_justified: bool = False,
        change_disclosed: bool = False
    ) -> List[GAAPViolation]:
        """
        Validate consistency principle: use same accounting methods across periods.
        
        Changes are allowed but must be justified and disclosed.
        
        Args:
            current_method: Current accounting method
            previous_method: Previous accounting method
            account_type: Type of account (e.g., "Inventory", "Depreciation")
            change_justified: Whether change has valid justification
            change_disclosed: Whether change was properly disclosed
            
        Returns:
            List of GAAPViolation objects
        """
        violations = []
        
        if current_method != previous_method:
            if not change_justified:
                violations.append(GAAPViolation(
                    principle="Consistency",
                    description=f"Accounting method for {account_type} changed from {previous_method} to {current_method} without justification",
                    severity="HIGH",
                    affected_account=account_type
                ))
            
            if not change_disclosed:
                violations.append(GAAPViolation(
                    principle="Full Disclosure",
                    description=f"Change in accounting method for {account_type} not properly disclosed in financial statements",
                    severity="MEDIUM",
                    affected_account=account_type
                ))
        
        return violations
