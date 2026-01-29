# brynq_sdk_sage_100_france

A Python SDK developed by BrynQ for integrating with Sage 100 France HR and Payroll systems. This package provides a streamlined interface for interacting with Sage 100 France databases.

## Overview

The brynq_sdk_sage_100_france package provides comprehensive access to Sage 100 France data through the BrynQ Agent API, enabling:

- Employee data management and retrieval
- Salary and payroll information access
- Contract management
- Import/export operations for Sage 100 France
- Comprehensive data validation using Pydantic and Pandera

## Installation

```bash
pip install brynq-sdk-sage-100-france
```

## Dependencies

- brynq-sdk-brynq>=4,<5
- pandas
- pandera
- pydantic
- requests

## Quick Start

```python
from brynq_sdk_sage_100_france import Sage100France

# Initialize the client
sage = Sage100France(
    subdomain="your_subdomain",
    api_token="your_api_token",
    connection_string="your_sage_connection_string"
)

# Get all employees with validation
valid_employees, invalid_employees = sage.employees.get()

# Get salary information
valid_salary, invalid_salary = sage.salary.get()

# Execute custom SQL queries
results = sage.execute_query([
    "SELECT * FROM T_CONTACT WHERE NumSalarie IS NOT NULL"
])
```

## Key Features

### Data Retrieval
- **Employee Management**: Access complete employee records from T_CONTACT table
- **Salary Information**: Retrieve salary data with automatic validation
- **Contract History**: Access employee contract information
- **Address Management**: Manage employee address information
- **Position Data**: Access job titles and positions
- **Family Information**: Retrieve family and dependent data
- **Absence & Leave Tracking**: Access absence and leave records
- **Service History**: Track employee service records
- **Department Data**: Organizational structure information
- **Bank Information**: Employee banking details
- **Company Data**: Company information management
- **Insurance Records**: Employee and company insurance data

### Import/Export Operations
- **Registration Data Import**: Import employee registration information
- **Civil Status Import**: Import civil status and family data (supports up to 99 children)
- **Time Page Import**: Import personnel record time page data
- **DADS-U Import**: Import DADS-U declaration data
- **Work Assignment Import**: Import work assignment information
- **Work Location Import**: Import work location data
- **Buffer System**: Accumulate multiple import operations before exporting
- **Fixed-Width Format**: Automatically formats data for Sage 100 France import

### Query Capabilities
- **Direct SQL Execution**: Execute custom SQL queries against the database
- **Query Builder**: Simple SELECT query builder with WHERE clause support
- **Multi-Query Support**: Execute multiple queries in a single request
- **Retry Strategy**: Automatic retry with exponential backoff for failed requests

### Data Validation
- **Schema Validation**: All data validated using Pandera DataFrameModels
- **Pydantic Models**: Request/response validation for import operations
- **Error Reporting**: Separate valid and invalid data for inspection
- **Type Coercion**: Automatic type conversion where possible

## Available Resources

### Core Methods
- `execute_query()` - Execute custom SQL queries
- `get()` - Simple query builder for SELECT operations
- `prepare_formatted_rows()` - Format data for import
- `add_rows_to_buffer()` - Add formatted rows to buffer
- `export_buffer_to_file()` - Export buffer to file
- `clear_buffer()` - Clear the buffer
- `get_buffer_content()` - Get current buffer content

### Data Access
- **employees** - Employee data and import operations
  - `get()` - Get all employees
  - `import_registration_data()` - Import registration data
  - `import_civil_status_data()` - Import civil status
  - `import_time_page_data()` - Import time page data
  - `import_dads_u_data()` - Import DADS-U data
  - `work` - Work-related sub-module
    - `import_assignment_data()` - Import work assignments
    - `import_work_location_data()` - Import work locations
  - `insurance` - Employee insurance sub-module
    - `get()` - Get employee insurance records
- **salary** - Salary information
- **contract** - Contract management
- **address** - Address information
- **position** - Position/job title data
- **family** - Family information
- **absence** - Absence tracking
- **leave** - Leave management
- **service** - Service history
- **department** - Department data
- **bank_info** - Bank account information
- **company** - Company details
- **insurance** - Insurance information
- **employee_insurance** - Employee insurance records

## Usage Examples

### Retrieving Data

```python
# Get employee data with validation
valid_data, invalid_data = sage.employees.get()
print(f"Valid employees: {len(valid_data)}")
print(f"Invalid employees: {len(invalid_data)}")

# Get salary records
valid_salary, invalid_salary = sage.salary.get()

# Get contract information
contracts = sage.contract.get()
```

### Custom SQL Queries

```python
# Execute a single query
results = sage.execute_query([
    "SELECT IdContact, Nom, Prenom, Mel FROM T_CONTACT WHERE TypeContact = 0"
])

# Execute multiple queries
results = sage.execute_query([
    "SELECT * FROM T_SAL WHERE MontantSal > 3000",
    "SELECT * FROM T_HST_CONTRAT WHERE DateDebut > '2023-01-01'"
])
```

### Query Builder

```python
# Get all columns from a table
all_data = sage.get(table_name="T_CONTACT")

# Get specific columns with WHERE clause
filtered_data = sage.get(
    table_name="T_CONTACT",
    columns=["IdContact", "Nom", "Prenom", "Mel"],
    where_clause="TypeContact = 0 AND Nom LIKE 'D%'"
)
```

### Import Operations

```python
import pandas as pd

# Prepare registration data
registration_df = pd.DataFrame({
    'employee_id': ['EMP001', 'EMP002'],
    'last_name': ['Dupont', 'Martin'],
    'first_name': ['Jean', 'Marie'],
    'email_address': ['jean.dupont@example.com', 'marie.martin@example.com'],
    'address_1': ['123 Rue de la Paix', '456 Avenue des Champs'],
    'address_1_city': ['Paris', 'Lyon'],
    'address_1_postal_code': ['75001', '69001']
})

# Import to buffer
sage.employees.import_registration_data(registration_df)

# Prepare civil status data
civil_status_df = pd.DataFrame({
    'employee_id': ['EMP001'],
    'marital_status': [1],
    'number_of_children': [2],
    'child_1_first_name': ['Sophie'],
    'child_1_last_name': ['Dupont'],
    'child_1_birth_date': ['15/05/2015'],
    'child_1_gender': [2],
    'child_1_dependent': [1]
})

# Import to buffer
sage.employees.import_civil_status_data(civil_status_df)

# Export all buffered data to file
sage.export_buffer_to_file('sage_import.txt')

# Clear buffer for next operation
sage.clear_buffer()
```

### Work Management

```python
# Import work assignment
assignment_df = pd.DataFrame({
    'employee_id': ['EMP001'],
    'assignment_type': ['CADRE'],
    'start_date': ['01/01/2024']
})
sage.employees.work.import_assignment_data(assignment_df)

# Import work location
location_df = pd.DataFrame({
    'employee_id': ['EMP001'],
    'location_code': ['LOC001'],
    'location_name': ['Siège Social']
})
sage.employees.work.import_work_location_data(location_df)

# Export to file
sage.export_buffer_to_file('work_import.txt')
sage.clear_buffer()
```

## Environment Variables

You can also configure the client using environment variables:

```bash
export BRYNQ_SUBDOMAIN="your_subdomain"
export BRYNQ_API_TOKEN="your_api_token"
export SAGE100_CONNECTION_STRING="your_sage_connection_string"
```

Then initialize without parameters:

```python
sage = Sage100France()
```

## Data Format Notes

- **Date Format**: Import operations use `dd/mm/yy` format
- **Decimal Separator**: Comma (`,`) is used for decimal values
- **Decimal Places**: 3 decimal places for numeric values
- **Fixed-Width Format**: Import files use position-based formatting
- **Child Data**: Civil status supports up to 99 children per employee
- **Automatic Codes**: Unique codes are automatically added based on record type
  - Registration: "01"
  - Civil Status: "02"
  - Work Location: "03"
  - Assignment: "04"
  - Time Page: "GT"
  - DADS-U: "DU"

## Error Handling

```python
from requests.exceptions import HTTPError

try:
    valid_data, invalid_data = sage.employees.get()

    if not invalid_data.empty:
        print(f"Warning: {len(invalid_data)} records failed validation")

except HTTPError as e:
    print(f"HTTP error: {e}")
except ValueError as e:
    print(f"Data processing error: {e}")
```

## Documentation

For detailed documentation, visit: [BrynQ SDK Documentation](https://docs.brynq.com)

## Support

For support and questions:
- Email: support@brynq.com
- Documentation: https://docs.brynq.com

## License

BrynQ License
