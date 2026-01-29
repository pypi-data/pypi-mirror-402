import pandera as pa
import pandas as pd
from pandera.typing import Series, String, Int, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class FamilySchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating family data from Sage 100 France T_HST_FAMILLE table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    family_history_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Family history identifier", alias="IdHstFamille")
    current_info: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Current information flag", alias="InfoEnCours")
    employee_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Employee number", alias="NumSalarie")

    # Date Information
    history_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="History date", alias="DateHist")
    start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Start date", alias="DateDebut")

    # Family Details
    family_situation: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Family situation", alias="SituationFamille")

    # Spouse/Partner Information
    civility: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Civility", alias="Civilite")
    last_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 80}, description="Last name", alias="Nom")
    maiden_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 80}, description="Maiden name", alias="NomJeuneFille")
    first_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="First name", alias="Prenom")
    birth_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Birth date", alias="DateNaissance")
    birth_department: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Birth department", alias="DeptNaissance")
    birth_country_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Birth country code", alias="CodePaysNaissance")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "family_history_id"
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
