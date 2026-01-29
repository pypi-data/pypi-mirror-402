import pandera as pa
import pandas as pd
from pandera.typing import Series, String, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class EmployeeInsuranceSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating employee insurance data from Sage 100 France T_SALARIE_CONTRAT_SOCIAL table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Keys
    employee_insurance_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Employee insurance identifier", alias="EmployeeInsuranceId")
    employee_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Employee identifier", alias="EmployeeId")
    insurance_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Insurance identifier", alias="InsuranceId")

    # Affiliation Details
    affiliation_reference: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 50}, description="Affiliation reference", alias="AffiliationReference")
    option_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Option code", alias="OptionCode")
    population_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Population code", alias="PopulationCode")

    # Beneficiaries
    dependent_children: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Number of dependent children", alias="DependentChildren")
    adult_beneficiaries: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Number of adult beneficiaries", alias="AdultBeneficiaries")
    total_beneficiaries: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Total number of beneficiaries", alias="TotalBeneficiaries")
    other_beneficiaries: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Number of other beneficiaries", alias="OtherBeneficiaries")
    child_beneficiaries: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Number of child beneficiaries", alias="ChildBeneficiaries")

    # Validity Period
    start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Start date", alias="StartDate")
    end_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="End date", alias="EndDate")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "employee_insurance_id"
        foreign_keys = {
            "employee_id": {
                "parent_schema": "EmployeeSchema",
                "parent_column": "employee_id",
                "cardinality": "N:1"
            },
            "insurance_id": {
                "parent_schema": "InsuranceSchema",
                "parent_column": "insurance_id",
                "cardinality": "N:1"
            }
        }

    class Config:
        """Schema configuration"""
        strict = True
        coerce = True
