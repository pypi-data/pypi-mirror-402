"""Schema definitions for Sage 100 France package"""

# Employee schemas
from .employee import (
    EmployeeSchema,
    RegistrationSchema,
    CivilStatusSchema,
    PersonnelRecordTimePageSchema,
    DadsUSchema
)

# Salary schemas
from .salary import (
    SalaryGetSchema,
    SalarySchema,
    WithholdingTaxSchema,
    TaxSchema,
    LeaveSchema as SalaryLeaveSchema  # Alias to avoid conflict with leave.LeaveSchema
)

# Work schemas
from .work import (
    WorkLocationSchema,
    AssignmentSchema
)

# Other schemas
from .address import AddressSchema
from .position import PositionSchema
from .family import FamilySchema
from .absence import AbsenceSchema
from .leave import LeaveSchema
from .service import ServiceSchema
from .department import DepartmentSchema
from .bank_info import BankInfoSchema
from .company import CompanySchema
from .contract import ContractSchema
from .insurance import InsuranceSchema
from .employee_insurance import EmployeeInsuranceSchema

__all__ = [
    # Employee schemas
    "EmployeeSchema",
    "RegistrationSchema",
    "CivilStatusSchema",
    "PersonnelRecordTimePageSchema",
    "DadsUSchema",
    # Salary schemas
    "SalaryGetSchema",
    "SalarySchema",
    "WithholdingTaxSchema",
    "TaxSchema",
    "SalaryLeaveSchema",  # Import-specific schema from salary.py
    # Work schemas
    "WorkLocationSchema",
    "AssignmentSchema",
    # Other schemas
    "AddressSchema",
    "PositionSchema",
    "FamilySchema",
    "AbsenceSchema",
    "LeaveSchema",  # Main leave schema from leave.py
    "ServiceSchema",
    "DepartmentSchema",
    "BankInfoSchema",
    "CompanySchema",
    "ContractSchema",
    "InsuranceSchema",
    "EmployeeInsuranceSchema",
]
