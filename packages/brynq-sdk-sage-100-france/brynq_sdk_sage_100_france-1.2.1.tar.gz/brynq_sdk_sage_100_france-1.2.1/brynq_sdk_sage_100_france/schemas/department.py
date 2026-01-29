import pandera as pa
import pandas as pd
from pandera.typing import Series, String
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class DepartmentSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating department data from Sage 100 France T_DEPARTEMENT table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    organization_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Organization identifier", alias="IdOrg")
    code: Series[String] = pa.Field(coerce=True, nullable=False, str_length={"max_value": 10}, description="Department code", alias="Code")

    # Description
    title: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Department title", alias="Intitule")

    # Additional Information
    general_info_flag: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="General information flag", alias="FlagInfosgenerales")
    distribution_point_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Distribution point code", alias="CodePointDistribution")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "organization_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        strict = True  # Ensure no additional columns are present
        coerce = True  # Try to coerce types when possible
