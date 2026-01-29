import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel
from pandera.typing import Series, String, DateTime

class AddressSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating address data from Sage 100 France T_HST_ADRESSE table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    address_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Address history identifier", alias="IdHstAdresse")
    current_info: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Current information flag", alias="InfoEnCours")
    employee_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Employee number", alias="NumSalarie")

    # Date Information
    history_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="History date", alias="DateHist")
    start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Start date", alias="DateDebut")

    # Address Information
    street_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Street address line 1", alias="Rue1")
    street_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Street address line 2", alias="Rue2")
    city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="City", alias="Commune")
    distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Distribution office", alias="BureauDistributeur")
    postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 8}, description="Postal code", alias="CodePostal")
    country: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Country", alias="Pays")

    # Contact Information
    phone_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Primary phone number", alias="Telephone1")

    # Additional Information
    foreign_distribution_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 50}, description="Foreign distribution code", alias="CodeDistribuALEtranger")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "address_id"
        foreign_keys = {
            "employee_number": {
                "parent_schema": "EmployeeSchema",
                "parent_column": "employee_number",
                "cardinality": "N:1"
            }
        }

    class Config:
        """Schema configuration"""
        strict = True  # Ensure no additional columns are present
        coerce = True  # Try to coerce types when possible
