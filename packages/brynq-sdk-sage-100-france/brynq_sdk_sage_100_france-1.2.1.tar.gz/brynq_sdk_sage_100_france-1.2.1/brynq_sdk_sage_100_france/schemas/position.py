import pandera as pa
import pandas as pd
from pandera.typing import Series, String, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class PositionSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating position data from Sage 100 France T_POSTES table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    position_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Position identifier", alias="IdPoste")
    code: Series[String] = pa.Field(coerce=True, nullable=False, str_length={"max_value": 10}, description="Position code", alias="Code")

    # Position Details
    title: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 60}, description="Position title", alias="Intitule")
    parent_position: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Parent position", alias="PostePere")
    creation_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Creation date", alias="DateCreation")
    status: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Status", alias="Statut")

    # Classification
    job_type: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Job type", alias="EmploiType")
    department: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Department", alias="Departement")
    service: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Service", alias="Service")
    unit: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Unit", alias="Unite")
    category: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Category", alias="Categorie")

    # Additional Information
    establishment_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Establishment code", alias="CodeEtab")
    general_info_flag: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="General information flag", alias="FlagInfosGenerales")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "position_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        strict = True  # Ensure no additional columns are present
        coerce = True  # Try to coerce types when possible
