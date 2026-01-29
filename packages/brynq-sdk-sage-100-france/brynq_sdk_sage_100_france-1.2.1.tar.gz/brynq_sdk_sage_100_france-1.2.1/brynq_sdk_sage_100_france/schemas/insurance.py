import pandera as pa
import pandas as pd
from pandera.typing import Series, String, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class InsuranceSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating insurance data from Sage 100 France T_CONTRAT_SOCIAL table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Insurance Contract Identity
    insurance_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Insurance identifier", alias="InsuranceId")
    contract_code: Series[String] = pa.Field(coerce=True, nullable=False, str_length={"max_value": 20}, description="Contract code", alias="ContractCode")
    contract_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 100}, description="Contract name", alias="ContractName")

    # Contract Details
    contract_reference: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 50}, description="Contract reference", alias="ContractReference")
    insurance_type: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Insurance type", alias="InsuranceType")
    provider_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 100}, description="Provider name", alias="ProviderName")

    # Validity Period
    start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Start date", alias="StartDate")
    end_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="End date", alias="EndDate")

    # Status
    is_active: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=1, description="Active status", alias="IsActive")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "insurance_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        strict = True
        coerce = True
