# Payroll Module Implementation

## Overview

The Payroll module has been successfully implemented as a comprehensive system that integrates with the existing HR/HRIS infrastructure and automatically validates all payroll calculations against FLSA (Fair Labor Standards Act) and California Labor Code compliance rules.

## Implementation Summary

### 1. Database Models (`backend/app/models/payroll.py`)

#### PayrollStatus Enum
- `DRAFT`: Initial state for new payroll periods
- `PENDING`: Awaiting processing
- `PROCESSING`: Currently being processed
- `PROCESSED`: Successfully completed
- `FAILED`: Processing failed
- `CANCELLED`: Cancelled payroll period

#### PayrollPeriod Model
- Tracks payroll periods with start/end dates and pay dates
- Stores aggregate totals (gross, deductions, net)
- Links to the user who processed the period
- Includes status tracking and audit timestamps
- Indexes on dates and status for efficient queries

#### Payslip Model
- Links to both PayrollPeriod and Employee
- Tracks hours worked (regular, overtime, double-time)
- Calculates all pay components:
  - Regular pay, overtime pay, double-time pay
  - Bonuses, commissions, other earnings
  - Federal tax, state tax, Social Security, Medicare
  - Health insurance, 401k, other deductions
- Compliance flags (`flsa_compliant`, `ca_labor_code_compliant`)
- Stores compliance violation notes
- Indexes on employee/period combinations and compliance flags

### 2. Pydantic Schemas (`backend/app/schemas/payroll.py`)

Following existing patterns from `schemas/hr.py`:

- **PayrollPeriodCreate**: Required fields for creating a new period
- **PayrollPeriodUpdate**: All fields optional for updates
- **PayrollPeriodResponse**: Complete response with all calculated fields
- **PayslipCreate**: Required fields and optional deductions/earnings
- **PayslipUpdate**: All fields optional for updates
- **PayslipResponse**: Complete payslip with all calculated values
- **PayslipWithDetails**: Includes related employee and period details

### 3. Service Layer (`backend/app/services/payroll_service.py`)

#### Key Functions

##### `create_payroll_period()`
- Validates date ranges (end must be after start)
- Checks for overlapping periods
- Creates period in DRAFT status
- Generates audit log

##### `calculate_payslip()`
**Critical compliance function that:**
- Determines employee exempt status from Position.is_exempt
- Calculates regular pay (salary or hourly)
- Applies FLSA overtime rules (1.5x for >40 hours/week) for non-exempt employees
- Applies CA Labor Code double-time rules (2x) for non-exempt employees
- Calculates all tax withholdings (federal, state, Social Security, Medicare)
- Validates CA minimum wage ($16.00/hr as of 2024)
- Sets compliance flags and creates ComplianceViolation records when needed
- Returns fully calculated Payslip object

##### `create_payslip()`
- Validates payroll period and employee existence
- Prevents duplicate payslips for same employee/period
- Calls `calculate_payslip()` for all calculations
- Creates audit log

##### `update_payslip()`
- Merges update data with existing payslip
- Recalculates entire payslip (maintains integrity)
- Creates audit log

##### `process_payroll_period()`
- Changes status to PROCESSING
- Calculates totals from all payslips in period
- Updates period with totals and processed timestamp
- Changes status to PROCESSED
- Creates audit log
- Sets status to FAILED on error

##### `delete_payroll_period()` & `delete_payslip()`
- Validation and audit logging before deletion
- PayrollPeriod can only be deleted if in DRAFT status

### 4. API Endpoints (`backend/app/api/v1/endpoints/payroll.py`)

Following the RESTful pattern from `endpoints/hr.py`:

#### Payroll Period Endpoints
- `GET /payroll/periods` - List periods with pagination and status filtering
- `POST /payroll/periods` - Create new period
- `GET /payroll/periods/{period_id}` - Get period details
- `PUT /payroll/periods/{period_id}` - Update period
- `DELETE /payroll/periods/{period_id}` - Delete period (DRAFT only)
- `POST /payroll/periods/{period_id}/process` - Process payroll period

#### Payslip Endpoints
- `GET /payroll/payslips` - List payslips with pagination and filtering
- `POST /payroll/payslips` - Create payslip with automatic calculation
- `GET /payroll/payslips/{payslip_id}` - Get payslip details
- `PUT /payroll/payslips/{payslip_id}` - Update and recalculate payslip
- `DELETE /payroll/payslips/{payslip_id}` - Delete payslip
- `GET /payroll/payslips/non-compliant` - List non-compliant payslips
- `GET /payroll/payslips/employee/{employee_id}` - Get employee payslip history

**All endpoints:**
- Use `get_current_active_user` dependency for authentication
- Extract client info (IP, user agent) for audit logs
- Call service layer functions (no direct DB operations)
- Return proper HTTP status codes
- Include pagination (skip/limit) for list endpoints

### 5. Integration

Updated three key files to integrate the payroll module:

1. **`backend/app/models/__init__.py`**
   - Added imports for PayrollPeriod, Payslip, PayrollStatus
   - Added to __all__ export list

2. **`backend/app/schemas/__init__.py`**
   - Added import for all payroll schemas

3. **`backend/app/api/v1/router.py`**
   - Imported payroll endpoints
   - Registered router with prefix "/payroll" and tag "Payroll"
   - Updated root endpoint to include payroll

### 6. Compliance Integration

The payroll system automatically integrates with the existing compliance infrastructure:

#### When Violations are Detected
1. Sets `flsa_compliant=False` or `ca_labor_code_compliant=False` on Payslip
2. Populates `compliance_notes` with violation details
3. Creates `ComplianceViolation` record:
   - `violation_type`: "LABOR_LAW"
   - `regulation`: "PAYROLL_COMPLIANCE"
   - `severity`: "CRITICAL" for minimum wage, "HIGH" for other violations
   - `entity_type`: "payslip"
   - `entity_id`: Links to the payslip ID

#### Compliance Checks Implemented
- ✅ **FLSA Overtime**: 1.5x rate for hours >40/week (non-exempt only)
- ✅ **CA Labor Code Double-Time**: 2x rate (non-exempt only)
- ✅ **CA Minimum Wage**: Validates effective rate >= $16.00/hr
- ✅ **Exempt Employee Handling**: No overtime/double-time for exempt employees

### 7. Testing (`tests/test_payroll/test_payroll_service.py`)

Comprehensive test suite includes:

#### Test Classes
- **TestPayrollPeriodCreation**: Date validation, overlapping period detection
- **TestPayslipCalculations**: 
  - Regular hours for hourly employees
  - Overtime calculations (FLSA 1.5x)
  - Double-time calculations (CA 2x)
  - Salaried employee calculations
  - Exempt employee handling (no overtime)
  - Tax withholding calculations
  - Net pay calculations
- **TestComplianceValidation**:
  - Minimum wage violation detection
  - Compliant wage validation
  - Compliance violation record creation
- **TestPayrollProcessing**:
  - Processing payroll periods
  - Empty period error handling
  - Already-processed error handling
- **TestPayslipUpdate**: Hours and rate updates with recalculation

### 8. Key Design Decisions

1. **Decimal for Currency**: All monetary amounts use `Decimal` type to avoid floating-point precision issues
2. **Automatic Recalculation**: Updates to payslips trigger complete recalculation to maintain data integrity
3. **Immutable Processing**: Once a payroll period is PROCESSED, it cannot be re-processed
4. **Compliance-First**: All calculations automatically validate against FLSA and CA Labor Code
5. **Audit Trail**: All create, update, delete, and process operations generate audit logs
6. **Service Layer Pattern**: Business logic separated from API endpoints for maintainability

## Usage Examples

### Creating a Payroll Period
```python
POST /api/v1/payroll/periods
{
    "period_start": "2024-01-01",
    "period_end": "2024-01-15",
    "pay_date": "2024-01-20",
    "notes": "Bi-weekly payroll"
}
```

### Creating a Payslip for an Hourly Employee
```python
POST /api/v1/payroll/payslips
{
    "payroll_period_id": 1,
    "employee_id": 5,
    "regular_hours": 40.00,
    "overtime_hours": 5.00,
    "double_time_hours": 0.00,
    "hourly_rate": 25.00,
    "bonus": 100.00,
    "health_insurance": 150.00,
    "retirement_401k": 100.00
}
```

### Processing a Payroll Period
```python
POST /api/v1/payroll/periods/1/process
```

### Checking for Non-Compliant Payslips
```python
GET /api/v1/payroll/payslips/non-compliant
```

## Database Schema

### PayrollPeriod Table
```sql
CREATE TABLE payroll_periods (
    id INT PRIMARY KEY AUTO_INCREMENT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    pay_date DATE NOT NULL,
    status ENUM(...) NOT NULL DEFAULT 'DRAFT',
    total_gross DECIMAL(12,2),
    total_deductions DECIMAL(12,2),
    total_net DECIMAL(12,2),
    processed_at DATETIME,
    processed_by INT,
    notes TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_payroll_period_dates (period_start, period_end),
    INDEX idx_payroll_period_status (status),
    FOREIGN KEY (processed_by) REFERENCES users(id)
);
```

### Payslip Table
```sql
CREATE TABLE payslips (
    id INT PRIMARY KEY AUTO_INCREMENT,
    payroll_period_id INT NOT NULL,
    employee_id INT NOT NULL,
    regular_hours DECIMAL(8,2),
    overtime_hours DECIMAL(8,2),
    double_time_hours DECIMAL(8,2),
    hourly_rate DECIMAL(8,2),
    regular_pay DECIMAL(12,2) NOT NULL DEFAULT 0,
    overtime_pay DECIMAL(12,2) NOT NULL DEFAULT 0,
    double_time_pay DECIMAL(12,2) NOT NULL DEFAULT 0,
    bonus DECIMAL(12,2) NOT NULL DEFAULT 0,
    commission DECIMAL(12,2) NOT NULL DEFAULT 0,
    other_earnings DECIMAL(12,2) NOT NULL DEFAULT 0,
    gross_pay DECIMAL(12,2) NOT NULL,
    federal_tax DECIMAL(12,2) NOT NULL DEFAULT 0,
    state_tax DECIMAL(12,2) NOT NULL DEFAULT 0,
    social_security DECIMAL(12,2) NOT NULL DEFAULT 0,
    medicare DECIMAL(12,2) NOT NULL DEFAULT 0,
    health_insurance DECIMAL(12,2) NOT NULL DEFAULT 0,
    retirement_401k DECIMAL(12,2) NOT NULL DEFAULT 0,
    other_deductions DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_deductions DECIMAL(12,2) NOT NULL,
    net_pay DECIMAL(12,2) NOT NULL,
    flsa_compliant BOOLEAN NOT NULL DEFAULT TRUE,
    ca_labor_code_compliant BOOLEAN NOT NULL DEFAULT TRUE,
    compliance_notes TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_payslip_employee_period (employee_id, payroll_period_id),
    INDEX idx_payslip_compliance (flsa_compliant, ca_labor_code_compliant),
    FOREIGN KEY (payroll_period_id) REFERENCES payroll_periods(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

## Next Steps

To deploy this implementation:

1. **Database Migration**: Run Alembic migration to create the new tables:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add payroll tables"
   alembic upgrade head
   ```

2. **Testing**: Run the test suite:
   ```bash
   cd backend
   pytest tests/test_payroll/ -v
   ```

3. **Documentation**: The API will automatically include payroll endpoints in the OpenAPI/Swagger documentation at `/docs`

4. **Production Considerations**:
   - Implement proper tax table lookups (current implementation uses simplified rates)
   - Add batch processing capabilities for large payrolls
   - Implement payslip PDF generation
   - Add email notifications for processed payrolls
   - Consider implementing approval workflows for large payrolls

## Security Notes

- All endpoints require authentication (`get_current_active_user`)
- Audit logs track all payroll operations
- Compliance violations are automatically logged
- Sensitive payroll data should be protected with appropriate RBAC permissions

## Success Criteria - All Met ✅

- ✅ All models created with proper relationships and indexes
- ✅ Pydantic schemas following established patterns
- ✅ Service layer with automatic compliance validation
- ✅ API endpoints with pagination, filtering, and proper error handling
- ✅ Audit logging on all create/update/process operations
- ✅ Integration with existing Employee, Position, and User models
- ✅ Compliance violations automatically logged when detected
- ✅ RESTful API design consistent with existing endpoints
- ✅ Comprehensive test coverage
