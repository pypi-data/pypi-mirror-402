import pandera as pa
import pandas as pd
from pandera.typing import Series, String
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class CompanySchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating company data from Sage 100 France T_SOCIETE table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Company Identity
    company_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Company identifier", alias="CompanyId")
    company_code: Series[String] = pa.Field(coerce=True, nullable=False, str_length={"max_value": 10}, description="Company code", alias="CompanyCode")
    company_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 100}, description="Company name", alias="CompanyName")

    # Legal Information
    siren: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 9}, description="SIREN number", alias="SIREN")
    nic: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="NIC number", alias="NIC")
    ape_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="APE code", alias="APE_Code")

    # Address Information
    address_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 100}, description="Address line 1", alias="Address1")
    address_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 100}, description="Address line 2", alias="Address2")
    postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Postal code", alias="PostalCode")
    city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 50}, description="City", alias="City")
    country: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 50}, description="Country", alias="Country")

    # Contact Information
    phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Phone number", alias="Phone")
    fax: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Fax number", alias="Fax")
    email: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 100}, description="Email address", alias="Email")

    # Statistics
    average_headcount: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Average headcount", alias="AverageHeadcount")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "company_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        strict = True
        coerce = True
