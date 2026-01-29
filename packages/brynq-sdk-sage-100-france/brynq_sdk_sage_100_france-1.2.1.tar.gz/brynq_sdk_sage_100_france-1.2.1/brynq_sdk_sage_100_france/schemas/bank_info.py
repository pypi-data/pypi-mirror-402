import pandera as pa
import pandas as pd
from pandera.typing import Series, String
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class BankInfoSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating bank information data from Sage 100 France T_INFOBANQUE table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    bank_info_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Bank information identifier", alias="IdInfoBanque")
    employee_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="NumSalarie")
    bank_info_type: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Bank information type", alias="TypeInfoBanque")
    establishment_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Establishment code", alias="CodeEtab")
    number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Number", alias="Numero")

    # Bank Account Details
    bank_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 17}, description="Bank code", alias="CodeBanque")
    branch_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 17}, description="Branch code", alias="CodeGuichet")
    account_number: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 11}, description="Account number", alias="NoCompte")
    check_key: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Check key", alias="Cle")
    format: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Format", alias="Format")
    country_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Country code", alias="CodePays")
    bic: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 11}, description="BIC code", alias="Bic")
    account_label: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Account label", alias="LibelleCompte")
    issuer_number: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 8}, description="Issuer number", alias="NoEmetteur")
    currency_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Currency code", alias="CodeDevise")

    # Bank Information
    branch_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Branch name", alias="NomGuichet")
    bank_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Bank name", alias="NomBanque")
    account_holder: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Account holder", alias="TitulaireCompte")

    # CFONB Format (French Banking Standards)
    cfonb_bank_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="CFONB bank code", alias="CFONB_CodeBanque")
    cfonb_branch_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="CFONB branch code", alias="CFONB_CodeGuichet")
    cfonb_account_number: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 11}, description="CFONB account number", alias="CFONB_NumeroDeCompte")
    cfonb_check_key: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="CFONB check key", alias="CFONB_Cle")

    # Additional Information
    general_info_flag: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="General information flag", alias="FlagInfosGenerales")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "bank_info_id"
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
