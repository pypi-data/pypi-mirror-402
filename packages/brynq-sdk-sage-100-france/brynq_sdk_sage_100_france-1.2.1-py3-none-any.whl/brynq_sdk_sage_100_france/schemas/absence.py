import pandera as pa
from brynq_sdk_functions import BrynQPanderaDataFrameModel
from pandera.typing import Series, String
import pandas as pd

class AbsenceSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating absence data from Sage 100 France T_MOTIFDABSENCE table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    id_tab: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Table identifier", alias="IdTab")
    code: Series[String] = pa.Field(coerce=True, nullable=False, str_length={"max_value": 10}, description="Absence code", alias="Code")

    # Description
    title: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 60}, description="Absence title/description", alias="Intitule")

    # Classification and Codes
    social_report_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Social report code", alias="CodeBilanSocial")
    assedic_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Unemployment insurance code", alias="CodeAssedic")
    dadsu_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="DADSU declaration code", alias="CodeDADSU")
    cp_fund_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Professional training fund code", alias="CodeCaisseCP")
    dna_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="DNA code", alias="CodeDNA")
    dsn_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="DSN (Social Nomination Declaration) code", alias="CodeDSN")

    # Additional Information
    general_info_flag: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="General information flag", alias="FlagInfosGenerales")
    visible: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Visibility flag", alias="visible")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "id_tab"
        foreign_keys = {
            # No foreign key relationships identified for absence codes
        }

    class Config:
        """Schema configuration"""
        strict = True  # Ensure no additional columns are present
        coerce = True  # Try to coerce types when possible
