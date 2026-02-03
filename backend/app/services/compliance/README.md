# JERP 2.0 Compliance Framework

## Overview

The JERP 2.0 Compliance Framework provides comprehensive compliance checking for labor laws and financial accounting standards. The framework includes:

- **California Labor Code** compliance engine
- **Federal FLSA** compliance engine  
- **GAAP** (US Generally Accepted Accounting Principles) validation engine
- **IFRS** (International Financial Reporting Standards) validation engine
- Real-time violation tracking and escalation
- Immutable audit logging integration
- RESTful API for compliance operations

## Architecture

### Components

```
compliance/
├── california_labor_code.py  # CA labor law rules
├── flsa.py                    # Federal FLSA rules
├── gaap.py                    # GAAP financial validation
├── ifrs.py                    # IFRS financial validation
├── compliance_service.py      # Central compliance service
├── violation_tracker.py       # Violation management
└── __init__.py
```

### Database Models

#### ComplianceViolation
Tracks all detected compliance violations with:
- Violation type (LABOR_LAW, GAAP, IFRS)
- Severity (CRITICAL, HIGH, MEDIUM, LOW)
- Standard reference (e.g., CA_LABOR_CODE_512)
- Resource information
- Resolution tracking
- Financial impact

#### ComplianceRule
Stores configurable compliance rules:
- Rule code and type
- Standard reference
- Active status
- Rule parameters (JSON)
- Effective/expiration dates

#### ComplianceCheckLog
Logs all compliance checks performed:
- Check type and resource
- Pass/fail status
- Violations found
- Execution time
- User who performed check

## Usage Examples

### 1. California Labor Code - Overtime Calculation

```python
from app.services.compliance import california_labor_code
from datetime import datetime

# Define hours worked per day
hours_worked = {
    "2024-01-01": 10,  # 10 hours on Monday
    "2024-01-02": 9,   # 9 hours on Tuesday
    "2024-01-03": 8,   # 8 hours on Wednesday
    "2024-01-04": 12,  # 12 hours on Thursday
    "2024-01-05": 8,   # 8 hours on Friday
    "2024-01-06": 8,   # 8 hours on Saturday
    "2024-01-07": 6,   # 6 hours on 7th day (Sunday)
}

# Define workweek
workweek = [
    datetime(2024, 1, 1),
    datetime(2024, 1, 2),
    datetime(2024, 1, 3),
    datetime(2024, 1, 4),
    datetime(2024, 1, 5),
    datetime(2024, 1, 6),
    datetime(2024, 1, 7),
]

# Calculate overtime
result = california_labor_code.calculate_overtime(hours_worked, workweek)

print(f"Regular hours: {result['regular_hours']}")
print(f"Overtime 1.5x: {result['overtime_1_5x_hours']}")
print(f"Overtime 2x: {result['overtime_2x_hours']}")
print(f"Violations: {result['violations']}")
```

**Output:**
```
Regular hours: 35.0
Overtime 1.5x: 18.0  # Includes 6 hours on 7th day at 1.5x
Overtime 2x: 8.0     # 4 hours over 12 on Thursday
Violations: [{'date': '2024-01-07', 'type': 'SEVENTH_DAY_WORK', ...}]
```

### 2. California Labor Code - Meal Break Validation

```python
from datetime import datetime

shift_start = datetime(2024, 1, 1, 8, 0)   # 8:00 AM
shift_end = datetime(2024, 1, 1, 18, 0)     # 6:00 PM

breaks = [
    {
        "type": "meal",
        "start": datetime(2024, 1, 1, 12, 0),  # 12:00 PM
        "end": datetime(2024, 1, 1, 12, 30)     # 12:30 PM
    },
    {
        "type": "rest",
        "start": datetime(2024, 1, 1, 10, 0),  # 10:00 AM
        "end": datetime(2024, 1, 1, 10, 10)     # 10:10 AM
    }
]

result = california_labor_code.validate_meal_breaks(shift_start, shift_end, breaks)

if result['compliant']:
    print("✓ Meal breaks compliant")
else:
    print("✗ Violations found:")
    for violation in result['violations']:
        print(f"  - {violation['description']}")
```

### 3. FLSA - Overtime and Minimum Wage

```python
from app.services.compliance import flsa
from decimal import Decimal

# Calculate FLSA overtime
hours = 45  # Weekly hours
rate = Decimal("15.00")

overtime_result = flsa.calculate_flsa_overtime(hours, rate)
print(f"Regular pay: ${overtime_result['regular_pay']}")
print(f"Overtime pay: ${overtime_result['overtime_pay']}")
print(f"Total pay: ${overtime_result['total_pay']}")

# Validate minimum wage
total_pay = Decimal("580.00")
hours_worked = 45
employee_type = "regular"

min_wage_result = flsa.validate_minimum_wage(total_pay, hours_worked, employee_type)
if min_wage_result['compliant']:
    print("✓ Minimum wage compliance met")
else:
    print("✗ Below minimum wage")
```

### 4. GAAP - Journal Entry Validation

```python
from app.services.compliance import gaap

journal_entry = {
    "date": "2024-01-15",
    "description": "Record accounts receivable payment",
    "debits": [
        {"account": "Cash", "amount": 5000.00}
    ],
    "credits": [
        {"account": "Accounts Receivable", "amount": 5000.00}
    ]
}

result = gaap.validate_journal_entry(journal_entry)

if result['compliant']:
    print("✓ Journal entry is balanced and valid")
else:
    print("✗ Violations found:")
    for violation in result['violations']:
        print(f"  - {violation['description']}")
```

### 5. GAAP - Balance Sheet Validation

```python
assets = {
    "Cash": 50000,
    "Accounts Receivable": 30000,
    "Inventory": 25000,
    "Equipment": 100000,
}

liabilities = {
    "Accounts Payable": 20000,
    "Notes Payable": 50000,
}

equity = {
    "Common Stock": 100000,
    "Retained Earnings": 35000,
}

result = gaap.validate_balance_sheet(assets, liabilities, equity)

print(f"Assets: ${result['total_assets']}")
print(f"Liabilities + Equity: ${result['total_liabilities'] + result['total_equity']}")
print(f"Balance: ${result['balance']}")
print(f"Compliant: {result['compliant']}")
```

### 6. IFRS 15 - Revenue Recognition

```python
from app.services.compliance import ifrs

contract = {
    "customer_id": 12345,
    "has_commercial_substance": True,
    "payment_probable": True,
    "transaction_price": 10000,
    "performance_obligations": [
        {
            "description": "Product delivery",
            "allocated_price": 7000,
            "satisfaction_method": "point_in_time",
            "control_transferred": True
        },
        {
            "description": "Installation service",
            "allocated_price": 3000,
            "satisfaction_method": "over_time",
            "progress_percentage": 50
        }
    ]
}

result = ifrs.validate_ifrs15_revenue(contract)
print(f"Revenue recognizable: ${result['revenue_recognizable']}")
print(f"Compliant: {result['compliant']}")
```

### 7. Using ComplianceService for Labor Compliance

```python
from app.services.compliance import ComplianceService
from app.core.database import SessionLocal

service = ComplianceService()
db = SessionLocal()

timesheet = {
    "state": "CA",
    "hours_worked": {
        "2024-01-01": 10,
        "2024-01-02": 9,
        "2024-01-03": 8,
    },
    "workweek": [
        datetime(2024, 1, 1),
        datetime(2024, 1, 2),
        datetime(2024, 1, 3),
    ],
    "shift_start": datetime(2024, 1, 1, 8, 0),
    "shift_end": datetime(2024, 1, 1, 18, 0),
    "breaks": [
        {"type": "meal", "start": datetime(2024, 1, 1, 12, 0), "end": datetime(2024, 1, 1, 12, 30)}
    ],
    "regular_rate": 20.00,
    "total_pay": 540.00,
}

result = service.check_labor_compliance(
    employee_id=101,
    timesheet=timesheet,
    db=db,
    user_id=1
)

print(f"Compliant: {result['compliant']}")
print(f"Violations: {len(result['violations'])}")
print(f"Checks performed: {result['checks_performed']}")

db.close()
```

### 8. Using ViolationTracker

```python
from app.services.compliance import ViolationTracker
from app.core.database import SessionLocal

db = SessionLocal()
tracker = ViolationTracker(db)

# Check for violations needing escalation
escalations = tracker.check_escalations()
print(f"Violations needing escalation: {len(escalations)}")

for escalation in escalations:
    print(f"- Violation #{escalation['violation_id']}: {escalation['escalation_reason']}")

# Get analytics
analytics = tracker.get_violation_analytics()
print(f"\nTotal violations in last 30 days: {analytics['summary']['total']}")
print(f"Resolved: {analytics['summary']['resolved']}")
print(f"Unresolved: {analytics['summary']['unresolved']}")
print(f"Avg resolution time: {analytics['summary']['avg_resolution_time_hours']} hours")

# Resolve a violation
result = tracker.resolve_violation(
    violation_id=123,
    resolution_notes="Updated payroll calculation to include overtime",
    resolved_by=1
)

if result['success']:
    print(f"✓ Violation resolved in {result['resolution_time_hours']} hours")

db.close()
```

## API Endpoints

### Labor Compliance Check
```
POST /api/v1/compliance/check/labor
```

**Request:**
```json
{
  "employee_id": 101,
  "state": "CA",
  "hours_worked": {
    "2024-01-01": 10,
    "2024-01-02": 9
  },
  "workweek": ["2024-01-01", "2024-01-02"],
  "shift_start": "2024-01-01T08:00:00",
  "shift_end": "2024-01-01T18:00:00",
  "breaks": [
    {
      "type": "meal",
      "start": "2024-01-01T12:00:00",
      "end": "2024-01-01T12:30:00"
    }
  ],
  "regular_rate": 20.0,
  "total_pay": 540.0
}
```

**Response:**
```json
{
  "employee_id": 101,
  "compliant": true,
  "violations": [],
  "california_labor_code": {
    "overtime": {...},
    "meal_breaks": {...},
    "rest_breaks": {...}
  },
  "flsa": {
    "overtime": {...},
    "minimum_wage": {...}
  }
}
```

### Financial Compliance Check
```
POST /api/v1/compliance/check/financial
```

**Request:**
```json
{
  "transaction_id": "JE-2024-001",
  "type": "journal_entry",
  "standard": "GAAP",
  "data": {
    "date": "2024-01-15",
    "description": "Record payment",
    "debits": [{"account": "Cash", "amount": 5000}],
    "credits": [{"account": "Accounts Receivable", "amount": 5000}]
  }
}
```

### Get Violations
```
GET /api/v1/compliance/violations?severity=CRITICAL&resolved=false
```

**Response:**
```json
{
  "total": 5,
  "violations": [
    {
      "id": 123,
      "violation_type": "LABOR_LAW",
      "severity": "CRITICAL",
      "standard": "CA_LABOR_CODE_512",
      "resource_type": "timesheet",
      "resource_id": "101",
      "description": "Meal break not taken before end of 5th hour",
      "detected_at": "2024-01-15T14:30:00",
      "resolved_at": null
    }
  ]
}
```

### Resolve Violation
```
POST /api/v1/compliance/violations/123/resolve
```

**Request:**
```json
{
  "resolution_notes": "Updated payroll system to enforce meal break scheduling"
}
```

### Generate Compliance Report
```
POST /api/v1/compliance/reports/compliance
```

**Request:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "violation_types": ["LABOR_LAW", "GAAP"]
}
```

### Get Violation Analytics
```
GET /api/v1/compliance/analytics?start_date=2024-01-01&end_date=2024-01-31
```

## Rule Configuration

Compliance rules are stored in the database and can be configured dynamically:

```python
from app.models.compliance import ComplianceRule
from datetime import datetime

# Create a new rule
rule = ComplianceRule(
    rule_code="CA_OVERTIME_DAILY_8",
    rule_type="LABOR",
    standard="CA_LABOR_CODE",
    description="California daily overtime: 1.5x for hours 8-12",
    is_active=True,
    severity="HIGH",
    parameters={
        "threshold_hours": 8,
        "overtime_multiplier": 1.5,
        "applies_to_states": ["CA"]
    },
    effective_date=datetime(2024, 1, 1)
)

db.add(rule)
db.commit()
```

## Violation Severity Classification

The framework automatically classifies violations by severity:

- **CRITICAL**: 
  - Meal/rest break violations
  - Minimum wage violations
  - Child labor violations
  - Balance sheet imbalances
  - Financial impact > $10,000

- **HIGH**:
  - Overtime calculation errors
  - Recordkeeping violations
  - Revenue recognition issues
  - Financial impact $1,000-$10,000

- **MEDIUM**:
  - Minor recordkeeping issues
  - Depreciation calculation errors
  - Financial impact $100-$1,000

- **LOW**:
  - Documentation issues
  - Financial impact < $100

## Auto-Escalation

Violations are automatically escalated based on age:

- **CRITICAL**: 1 day
- **HIGH**: 3 days
- **MEDIUM**: 7 days
- **LOW**: 14 days

Use the `/violations/escalations` endpoint to check for violations needing escalation.

## Audit Trail Integration

All compliance checks and violations are automatically logged to the immutable audit log system:

- Compliance checks logged to `ComplianceCheckLog`
- Violations logged to `ComplianceViolation`
- Audit trail entries created via `AuditLog.create_entry()`
- SHA-256 hash chain maintains integrity

## Performance Considerations

- Compliance checks execute in < 100ms on average
- Database indexes on frequently queried fields:
  - `violation_type`
  - `severity`
  - `detected_at`
  - `resource_type`
  - `resource_id`
- Use pagination for large result sets
- Consider caching frequently accessed rules

## Error Handling

The framework provides detailed error information:

```python
result = service.check_labor_compliance(...)

if not result['compliant']:
    for violation in result['violations']:
        print(f"Severity: {violation['severity']}")
        print(f"Standard: {violation['standard']}")
        print(f"Description: {violation['description']}")
```

## Testing

See `backend/tests/compliance/` for comprehensive test suites:

- `test_california_labor_code.py`
- `test_flsa.py`
- `test_gaap.py`
- `test_ifrs.py`
- `test_compliance_service.py`
- `test_violation_tracker.py`

## Adding New Compliance Rules

To add a new compliance rule:

1. **Add validation function** to appropriate engine:
   ```python
   def validate_new_rule(data: dict) -> dict:
       result = {"compliant": True, "violations": []}
       # Validation logic here
       return result
   ```

2. **Create database rule entry**:
   ```python
   rule = ComplianceRule(
       rule_code="NEW_RULE_CODE",
       rule_type="LABOR",  # or "FINANCIAL"
       standard="STANDARD_NAME",
       description="Rule description",
       is_active=True,
       severity="MEDIUM",
       parameters={},
       effective_date=datetime.utcnow()
   )
   ```

3. **Integrate into ComplianceService**:
   ```python
   # Add check in appropriate method
   if condition:
       result = engine.validate_new_rule(data)
       if not result['compliant']:
           violations.extend(result['violations'])
   ```

4. **Add tests**:
   ```python
   def test_new_rule():
       result = engine.validate_new_rule(test_data)
       assert result['compliant'] == expected_result
   ```

## Support

For questions or issues with the compliance framework:

1. Check this documentation
2. Review test files for examples
3. Check API documentation at `/api/v1/docs`
4. Submit issues to the project repository

## Changelog

- **v2.0.0** (2024-01-15): Initial compliance framework implementation
  - California Labor Code engine
  - Federal FLSA engine
  - GAAP validation engine
  - IFRS validation engine
  - Violation tracking system
  - RESTful API endpoints
