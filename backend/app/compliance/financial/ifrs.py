"""
JERP 2.0 - IFRS (International Financial Reporting Standards) Validation Engine
Implements IFRS compliance checks for financial transactions and statements
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class IFRSInventoryMethod(str, Enum):
    """Inventory valuation methods allowed under IFRS (no LIFO)"""
    FIFO = "FIFO"  # First In, First Out
    AVERAGE_COST = "AVERAGE_COST"  # Weighted Average
    SPECIFIC_IDENTIFICATION = "SPECIFIC_IDENTIFICATION"
    # Note: LIFO is NOT permitted under IFRS


class IFRSDepreciationMethod(str, Enum):
    """Depreciation methods under IFRS (component-based)"""
    STRAIGHT_LINE = "STRAIGHT_LINE"
    DIMINISHING_BALANCE = "DIMINISHING_BALANCE"
    UNITS_OF_PRODUCTION = "UNITS_OF_PRODUCTION"


class IFRSAssetCategory(str, Enum):
    """IFRS asset categories"""
    PROPERTY = "PROPERTY"
    PLANT = "PLANT"
    EQUIPMENT = "EQUIPMENT"
    INTANGIBLE = "INTANGIBLE"


@dataclass
class IFRSViolation:
    """Represents an IFRS compliance violation"""
    standard: str  # e.g., "IAS 2", "IFRS 15"
    description: str
    severity: str
    affected_account: Optional[str] = None
    amount: Optional[Decimal] = None


@dataclass
class ComponentDepreciation:
    """Component-based depreciation (required by IAS 16)"""
    component_name: str
    component_cost: Decimal
    useful_life: int
    depreciation_method: IFRSDepreciationMethod


class IFRS:
    """
    International Financial Reporting Standards (IFRS) validation engine.
    
    Key standards implemented:
    - IAS 1: Presentation of Financial Statements
    - IAS 2: Inventories
    - IAS 16: Property, Plant and Equipment
    - IAS 38: Intangible Assets
    - IFRS 9: Financial Instruments
    - IFRS 15: Revenue from Contracts with Customers
    """
    
    # Materiality threshold
    MATERIALITY_THRESHOLD_PCT = Decimal("0.05")  # 5%
    
    def __init__(self):
        """Initialize IFRS validation engine"""
        pass
    
    def validate_inventory_method(
        self,
        method: str
    ) -> List[IFRSViolation]:
        """
        Validate inventory valuation method (LIFO not allowed under IFRS).
        
        IAS 2: Inventories - LIFO is prohibited
        
        Args:
            method: Inventory valuation method
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        if method.upper() == "LIFO":
            violations.append(IFRSViolation(
                standard="IAS 2",
                description="LIFO inventory method is not permitted under IFRS",
                severity="CRITICAL",
                affected_account="Inventory"
            ))
        
        allowed_methods = [m.value for m in IFRSInventoryMethod]
        if method.upper() not in allowed_methods:
            violations.append(IFRSViolation(
                standard="IAS 2",
                description=f"Invalid inventory method '{method}'. Allowed methods: {', '.join(allowed_methods)}",
                severity="HIGH",
                affected_account="Inventory"
            ))
        
        return violations
    
    def validate_inventory_valuation(
        self,
        method: str,
        cost: Decimal,
        net_realizable_value: Decimal,
        recorded_value: Decimal
    ) -> List[IFRSViolation]:
        """
        Validate inventory is valued at lower of cost or net realizable value.
        
        IAS 2: Inventories must be measured at lower of cost and NRV
        
        Args:
            method: Inventory method used
            cost: Cost of inventory
            net_realizable_value: Estimated selling price minus completion/selling costs
            recorded_value: Value recorded in books
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        # Check LIFO prohibition
        violations.extend(self.validate_inventory_method(method))
        
        # Lower of cost or NRV rule
        correct_value = min(cost, net_realizable_value)
        
        if recorded_value > correct_value:
            violations.append(IFRSViolation(
                standard="IAS 2",
                description=f"Inventory overvalued. Recorded: ${recorded_value}, Should be: ${correct_value} (lower of cost ${cost} or NRV ${net_realizable_value})",
                severity="HIGH",
                affected_account="Inventory",
                amount=recorded_value - correct_value
            ))
        
        return violations
    
    def validate_component_depreciation(
        self,
        asset_name: str,
        total_cost: Decimal,
        components: List[ComponentDepreciation]
    ) -> List[IFRSViolation]:
        """
        Validate component-based depreciation (required by IAS 16).
        
        IAS 16: Each significant component must be depreciated separately
        
        Args:
            asset_name: Name of the asset
            total_cost: Total cost of asset
            components: List of component depreciation details
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        if not components:
            violations.append(IFRSViolation(
                standard="IAS 16",
                description=f"Asset '{asset_name}' requires component-based depreciation under IFRS",
                severity="MEDIUM",
                affected_account=asset_name,
                amount=total_cost
            ))
            return violations
        
        # Validate components add up to total cost
        component_total = sum(c.component_cost for c in components)
        difference = abs(total_cost - component_total)
        
        if difference > Decimal("0.01"):
            violations.append(IFRSViolation(
                standard="IAS 16",
                description=f"Component costs (${component_total}) don't match total asset cost (${total_cost})",
                severity="HIGH",
                affected_account=asset_name,
                amount=difference
            ))
        
        # Validate each component has reasonable useful life
        for component in components:
            if component.useful_life < 1:
                violations.append(IFRSViolation(
                    standard="IAS 16",
                    description=f"Component '{component.component_name}' has invalid useful life of {component.useful_life} years",
                    severity="HIGH",
                    affected_account=asset_name
                ))
        
        return violations
    
    def validate_property_plant_equipment(
        self,
        asset_name: str,
        initial_cost: Decimal,
        accumulated_depreciation: Decimal,
        carrying_amount: Decimal,
        fair_value: Optional[Decimal] = None,
        revaluation_model: bool = False
    ) -> List[IFRSViolation]:
        """
        Validate Property, Plant & Equipment accounting (IAS 16).
        
        IAS 16 allows choice between:
        - Cost model: Cost less accumulated depreciation
        - Revaluation model: Fair value at revaluation date less subsequent depreciation
        
        Args:
            asset_name: Name of asset
            initial_cost: Original cost
            accumulated_depreciation: Total depreciation
            carrying_amount: Current book value
            fair_value: Fair value (if using revaluation model)
            revaluation_model: Whether using revaluation model
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        if revaluation_model:
            # Revaluation model: carrying amount should reflect fair value
            if fair_value is None:
                violations.append(IFRSViolation(
                    standard="IAS 16",
                    description=f"Asset '{asset_name}' uses revaluation model but no fair value provided",
                    severity="HIGH",
                    affected_account=asset_name
                ))
            elif abs(carrying_amount - fair_value) > fair_value * Decimal("0.05"):
                violations.append(IFRSViolation(
                    standard="IAS 16",
                    description=f"Asset '{asset_name}' carrying amount (${carrying_amount}) significantly differs from fair value (${fair_value})",
                    severity="MEDIUM",
                    affected_account=asset_name,
                    amount=abs(carrying_amount - fair_value)
                ))
        else:
            # Cost model: carrying amount = cost - accumulated depreciation
            expected_carrying = initial_cost - accumulated_depreciation
            
            if abs(carrying_amount - expected_carrying) > Decimal("0.01"):
                violations.append(IFRSViolation(
                    standard="IAS 16",
                    description=f"Asset '{asset_name}' carrying amount (${carrying_amount}) incorrect. Expected: ${expected_carrying}",
                    severity="HIGH",
                    affected_account=asset_name,
                    amount=abs(carrying_amount - expected_carrying)
                ))
        
        return violations
    
    def validate_intangible_assets(
        self,
        asset_name: str,
        is_internally_generated: bool,
        cost: Decimal,
        has_indefinite_life: bool,
        amortization_applied: bool,
        impairment_tested: bool
    ) -> List[IFRSViolation]:
        """
        Validate intangible asset accounting (IAS 38).
        
        IAS 38 rules:
        - Research costs must be expensed
        - Development costs can be capitalized if criteria met
        - Indefinite life intangibles not amortized but tested for impairment annually
        - Finite life intangibles amortized over useful life
        
        Args:
            asset_name: Name of intangible asset
            is_internally_generated: Whether generated internally
            cost: Capitalized cost
            has_indefinite_life: Whether asset has indefinite useful life
            amortization_applied: Whether amortization has been applied
            impairment_tested: Whether impairment testing performed
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        if has_indefinite_life:
            # Indefinite life: no amortization, but must test for impairment
            if amortization_applied:
                violations.append(IFRSViolation(
                    standard="IAS 38",
                    description=f"Intangible asset '{asset_name}' with indefinite life should not be amortized",
                    severity="HIGH",
                    affected_account=asset_name
                ))
            
            if not impairment_tested:
                violations.append(IFRSViolation(
                    standard="IAS 38",
                    description=f"Intangible asset '{asset_name}' with indefinite life must be tested for impairment annually",
                    severity="HIGH",
                    affected_account=asset_name
                ))
        else:
            # Finite life: must be amortized
            if not amortization_applied:
                violations.append(IFRSViolation(
                    standard="IAS 38",
                    description=f"Intangible asset '{asset_name}' with finite life must be amortized",
                    severity="HIGH",
                    affected_account=asset_name
                ))
        
        return violations
    
    def validate_revenue_recognition_ifrs15(
        self,
        contract_exists: bool,
        performance_obligations_identified: bool,
        transaction_price_determined: bool,
        performance_obligations_satisfied: bool,
        revenue_amount: Decimal,
        revenue_recognized: Decimal
    ) -> List[IFRSViolation]:
        """
        Validate revenue recognition under IFRS 15.
        
        IFRS 15 five-step model:
        1. Identify the contract
        2. Identify performance obligations
        3. Determine transaction price
        4. Allocate transaction price
        5. Recognize revenue when obligations satisfied
        
        Args:
            contract_exists: Step 1 complete
            performance_obligations_identified: Step 2 complete
            transaction_price_determined: Step 3 complete
            performance_obligations_satisfied: Step 5 - obligations satisfied
            revenue_amount: Total transaction price
            revenue_recognized: Amount of revenue recognized
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        if not contract_exists:
            violations.append(IFRSViolation(
                standard="IFRS 15",
                description="Revenue recognized without valid contract",
                severity="CRITICAL",
                amount=revenue_recognized
            ))
        
        if not performance_obligations_identified:
            violations.append(IFRSViolation(
                standard="IFRS 15",
                description="Performance obligations not properly identified",
                severity="HIGH",
                amount=revenue_recognized
            ))
        
        if not transaction_price_determined:
            violations.append(IFRSViolation(
                standard="IFRS 15",
                description="Transaction price not properly determined",
                severity="HIGH",
                amount=revenue_recognized
            ))
        
        if revenue_recognized > Decimal("0") and not performance_obligations_satisfied:
            violations.append(IFRSViolation(
                standard="IFRS 15",
                description=f"Revenue of ${revenue_recognized} recognized before performance obligations satisfied",
                severity="CRITICAL",
                amount=revenue_recognized
            ))
        
        if performance_obligations_satisfied and revenue_recognized < revenue_amount:
            violations.append(IFRSViolation(
                standard="IFRS 15",
                description=f"Performance obligations satisfied but full revenue not recognized. Recognized: ${revenue_recognized}, Should be: ${revenue_amount}",
                severity="MEDIUM",
                amount=revenue_amount - revenue_recognized
            ))
        
        return violations
    
    def validate_financial_instruments_ifrs9(
        self,
        instrument_type: str,
        classification: str,
        measurement_basis: str,
        fair_value: Optional[Decimal],
        amortized_cost: Optional[Decimal]
    ) -> List[IFRSViolation]:
        """
        Validate financial instruments classification and measurement (IFRS 9).
        
        IFRS 9 classifications:
        - Amortized cost
        - Fair value through OCI (other comprehensive income)
        - Fair value through profit or loss
        
        Args:
            instrument_type: Type of financial instrument
            classification: IFRS 9 classification
            measurement_basis: How it's measured (fair value or amortized cost)
            fair_value: Fair value if applicable
            amortized_cost: Amortized cost if applicable
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        valid_classifications = ["AMORTIZED_COST", "FVOCI", "FVTPL"]
        
        if classification not in valid_classifications:
            violations.append(IFRSViolation(
                standard="IFRS 9",
                description=f"Invalid classification '{classification}'. Must be one of: {', '.join(valid_classifications)}",
                severity="HIGH",
                affected_account=instrument_type
            ))
        
        if classification == "AMORTIZED_COST":
            if measurement_basis != "AMORTIZED_COST":
                violations.append(IFRSViolation(
                    standard="IFRS 9",
                    description=f"Instrument classified as amortized cost but measured at {measurement_basis}",
                    severity="HIGH",
                    affected_account=instrument_type
                ))
            
            if amortized_cost is None:
                violations.append(IFRSViolation(
                    standard="IFRS 9",
                    description="Amortized cost measurement required but not provided",
                    severity="HIGH",
                    affected_account=instrument_type
                ))
        
        if classification in ["FVOCI", "FVTPL"]:
            if measurement_basis != "FAIR_VALUE":
                violations.append(IFRSViolation(
                    standard="IFRS 9",
                    description=f"Instrument classified as fair value but measured at {measurement_basis}",
                    severity="HIGH",
                    affected_account=instrument_type
                ))
            
            if fair_value is None:
                violations.append(IFRSViolation(
                    standard="IFRS 9",
                    description="Fair value measurement required but not provided",
                    severity="HIGH",
                    affected_account=instrument_type
                ))
        
        return violations
    
    def validate_presentation_ias1(
        self,
        has_balance_sheet: bool,
        has_income_statement: bool,
        has_cash_flow_statement: bool,
        has_equity_statement: bool,
        has_notes: bool,
        comparatives_included: bool
    ) -> List[IFRSViolation]:
        """
        Validate financial statement presentation requirements (IAS 1).
        
        IAS 1 requires complete set of financial statements:
        - Statement of financial position (balance sheet)
        - Statement of comprehensive income
        - Statement of changes in equity
        - Statement of cash flows
        - Notes (accounting policies and explanations)
        - Comparative information for prior period
        
        Args:
            Various boolean flags for statement components
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        if not has_balance_sheet:
            violations.append(IFRSViolation(
                standard="IAS 1",
                description="Statement of financial position (balance sheet) missing",
                severity="CRITICAL"
            ))
        
        if not has_income_statement:
            violations.append(IFRSViolation(
                standard="IAS 1",
                description="Statement of comprehensive income missing",
                severity="CRITICAL"
            ))
        
        if not has_cash_flow_statement:
            violations.append(IFRSViolation(
                standard="IAS 1",
                description="Statement of cash flows missing",
                severity="CRITICAL"
            ))
        
        if not has_equity_statement:
            violations.append(IFRSViolation(
                standard="IAS 1",
                description="Statement of changes in equity missing",
                severity="HIGH"
            ))
        
        if not has_notes:
            violations.append(IFRSViolation(
                standard="IAS 1",
                description="Notes to financial statements missing",
                severity="HIGH"
            ))
        
        if not comparatives_included:
            violations.append(IFRSViolation(
                standard="IAS 1",
                description="Comparative information for prior period not included",
                severity="HIGH"
            ))
        
        return violations
    
    def validate_fair_value_measurement(
        self,
        asset_name: str,
        fair_value: Decimal,
        valuation_technique: str,
        level_1_inputs: bool,
        level_2_inputs: bool,
        level_3_inputs: bool
    ) -> List[IFRSViolation]:
        """
        Validate fair value measurement and hierarchy disclosure.
        
        Fair value hierarchy (IFRS 13):
        - Level 1: Quoted prices in active markets
        - Level 2: Observable inputs other than quoted prices
        - Level 3: Unobservable inputs
        
        Args:
            asset_name: Name of asset/liability
            fair_value: Fair value amount
            valuation_technique: Technique used
            level_1_inputs: Uses Level 1 inputs
            level_2_inputs: Uses Level 2 inputs
            level_3_inputs: Uses Level 3 inputs
            
        Returns:
            List of IFRSViolation objects
        """
        violations = []
        
        # Must use at least one level of inputs
        if not (level_1_inputs or level_2_inputs or level_3_inputs):
            violations.append(IFRSViolation(
                standard="IFRS 13",
                description=f"Fair value hierarchy level not specified for '{asset_name}'",
                severity="HIGH",
                affected_account=asset_name
            ))
        
        # Level 1 is preferred (most reliable)
        if level_3_inputs and not level_1_inputs and not level_2_inputs:
            violations.append(IFRSViolation(
                standard="IFRS 13",
                description=f"Asset '{asset_name}' uses only Level 3 (unobservable) inputs. Consider using more observable inputs if available.",
                severity="LOW",
                affected_account=asset_name
            ))
        
        if not valuation_technique:
            violations.append(IFRSViolation(
                standard="IFRS 13",
                description=f"Valuation technique not disclosed for '{asset_name}'",
                severity="MEDIUM",
                affected_account=asset_name
            ))
        
        return violations
