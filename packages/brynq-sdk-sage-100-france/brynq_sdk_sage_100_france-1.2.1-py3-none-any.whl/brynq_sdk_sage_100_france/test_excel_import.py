from brynq_sdk_sage_100_france import Sage100France
from dotenv import load_dotenv
import os
import pandas as pd
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv()


# Custom schema with 5 fields matching your Excel
class MinimalEmployeeSchema(BaseModel):
    """
    Minimal custom schema - 5 fields:
    matricule, nom, surnom, prenom, Date de naissance

    IMPORTANT: Field order matters!
    For Sage 100 France import, fields MUST be defined in the EXACT order
    as they appear in the format definition.
    """
    # Fields in order as per format
    employee_number: Optional[str] = Field(default=None, alias="matricule")
    last_name: Optional[str] = Field(default=None, alias="nom")
    surname: Optional[str] = Field(default=None, alias="surnom")
    first_name: Optional[str] = Field(default=None, alias="prenom")
    birth_date: Optional[str] = Field(default=None, alias="Date de naissance")

    class Config:
        populate_by_name = True


def test_simple_excel_export():
    """
    Test Excel export with standard template (44 fields).

    Realistic workflow:
    1. Data comes as dict/list (from API, database, etc.)
    2. Convert to DataFrame for easy manipulation
    3. Validate and export to Excel
    """
    sage = Sage100France()

    # Create test data using English field names (matching schema)
    employee_data = [
        {
            # Fields 1-10
            "employee_number": "465",
            "address": "8, Rue Preschez",
            "address_2": "",
            "postal_code": "92210",
            "city": "ST CLOUD",
            "phone": "0142345678",
            "phone_2": "",
            "last_name": "ANSIEAU",
            "family_name": "YAKOKOKOKSKI",
            "first_name": "Pascale",

            # Fields 11-20
            "insee_city_code": "92064",
            "country_code": "FR",
            "paying_establishment": "001",
            "social_security_number": "274026992064123",
            "birth_date": "06/02/74",
            "marital_status": "M",
            "nationality_code": "0",
            "civility": "2",
            "contract_start_date": "02/12/19",
            "contract_nature": "CDI",

            # Fields 21-30
            "work_modality": "0",
            "profession_entry_date": "01/01/15",
            "profession_seniority": "8",
            "company_hire_date": "02/12/19",
            "establishment_entry_date": "02/12/19",
            "establishment_entry_type": "01",
            "seniority_date": "02/12/19",
            "last_worked_paid_day": "",
            "departure_reason": "",
            "conventional_termination_date": "",

            # Fields 31-40
            "company_departure_date": "",
            "establishment_exit_date": "",
            "employee_base_salary": "3750.00",
            "salary_type": "0",
            "annual_base_salary": "45000.00",
            "payment_periodicity": "5",
            "work_time_unit": "H",
            "activity_modality": "T",
            "account_number_1": "FR7630002005110001234567890",
            "bic_code_1": "CRLYFRPP",

            # Fields 41-44
            "account_label_1": "MME ANSIEAU",
            "branch_name_1": "PARIS OPERA",
            "branch_code_1": "00511",
            "payment_method": "VIR"
        }
    ]

    # Convert to DataFrame (more realistic workflow)
    df = pd.DataFrame(employee_data)

    # Validate and export to Excel
    output_excel = "scenerio_import.xlsx"
    result_path = sage.employees.export_to_excel(df, output_excel)

    print(f"✓ Output Excel file created: {result_path}")


def test_custom_schema_export():
    """Test Excel export with custom minimal schema (5 fields only)"""
    sage = Sage100France()

    # Minimal data with only 5 fields: matricule, nom, surnom, prenom, Date de naissance
    minimal_data = [
        {
            "employee_number": "1117",
            "last_name": "SDK jaap",
            "surname": "van hengel",
            "first_name": "van hengel",
            "birth_date": "01/01/2025"
        },
        {
            "employee_number": "1118",
            "last_name": "yakupski",
            "surname": "keskın",
            "first_name": "SDK Yakupski",
            "birth_date": "02/01/2025"
        },
        {
            "employee_number": "1119",
            "last_name": "jesse",
            "surname": "vd rıet",
            "first_name": "Sdk Jesse",
            "birth_date": "03/01/2025"
        }
    ]

    df = pd.DataFrame(minimal_data)

    # Use custom schema
    output_excel = "sdk_test_minimal_export.xlsx"
    result_path = sage.employees.export_to_excel(
        df,
        output_excel,
        schema=MinimalEmployeeSchema  # Custom schema with 5 fields!
    )

    print(f"✓ Custom schema export created: {result_path}")


if __name__ == "__main__":
    # Test custom schema export (5 fields only)
    #test_custom_schema_export()

    # Uncomment to test standard template (40 fields)
    test_simple_excel_export()
