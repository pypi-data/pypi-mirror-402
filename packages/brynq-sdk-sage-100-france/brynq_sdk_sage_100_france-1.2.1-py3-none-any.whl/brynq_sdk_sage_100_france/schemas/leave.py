import pandera as pa
import pandas as pd
from pandera.typing import Series, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class LeaveSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating leave data from Sage 100 France T_HST_CONGE table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    leave_history_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Leave history identifier", alias="IdHstConge")
    current_info: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Current information flag", alias="InfoEnCours")
    employee_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Employee number", alias="NumSalarie")

    # Date Information
    history_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="History date", alias="DateHist")
    leave_start_date_1: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Leave start date 1", alias="DateDebutConges1")
    leave_end_date_1: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Leave end date 1", alias="DateFinConges1")
    start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Start date", alias="DateDebut")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "leave_history_id"
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
