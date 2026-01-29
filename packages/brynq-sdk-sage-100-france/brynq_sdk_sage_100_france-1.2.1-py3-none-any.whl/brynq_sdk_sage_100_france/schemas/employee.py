from brynq_sdk_functions import BrynQPanderaDataFrameModel
from typing import Optional
from pydantic import BaseModel, Field
import pandas as pd
import pandera as pa
from pandera.typing import Series, String, Float,DateTime

class EmployeeSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating employee data from Sage 100 France T_CONTACT table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Identity and Classification
    contact_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Contact identifier", alias="IdContact")
    contact_code: Series[String] = pa.Field(coerce=True, nullable=False, str_length={"max_value": 10}, description="Contact code", alias="CodeContact")
    contact_type: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Contact type", alias="TypeContact")
    employee_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="NumSalarie")
    establishment_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Establishment code", alias="CodeEtab")

    # Company Information
    siren: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 9}, description="SIREN number", alias="SIREN")
    nic: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="NIC number", alias="NIC")

    # Personal Information
    civility: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, default=0, description="Civility", alias="Civilite")
    last_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 80}, description="Last name", alias="Nom")
    first_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="First name", alias="Prenom")
    quality: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Quality/Title", alias="Qualite")

    # Address Information
    street_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Street address line 1", alias="Rue1")
    street_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Street address line 2", alias="Rue2")
    city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="City", alias="Commune")
    distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Distribution office", alias="BureauDistributeur")
    postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 8}, description="Postal code", alias="CodePostal")
    country: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Country", alias="Pays")

    # Contact Information
    phone_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Primary phone number", alias="Telephone1")
    phone_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Secondary phone number", alias="Telephone2")
    telex: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Telex number", alias="Telex")
    fax: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Fax number", alias="Fax")
    email: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 60}, description="Email address", alias="Mel")

    # Additional Information
    comment: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 50}, description="Comment", alias="Commentaire")
    insee_city_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="INSEE city code", alias="CodeInseeCommune")
    general_info_flag: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="General information flag", alias="FlagInfosGenerales")
    quality_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Quality code", alias="CodeQualite")
    visible: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=  True, description="Visibility flag", alias="visible")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "contact_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        strict = True
        coerce = True

class EmployeeExcelImport(BaseModel):
    """
    Pydantic schema for Excel import/export of Employee data from Sage 100 France.
    Standard template with 44 fields in specified order.
    """

    # 1-10
    employee_number: Optional[str] = Field(default=None, alias="Matricule", description="Employee number")
    gender: Optional[int] = Field(default=None, alias="Sexe", description="Gender")
    address: Optional[str] = Field(default=None, alias="Adresse", description="Address")
    address_2: Optional[str] = Field(default=None, alias="Adresse 2", description="Address 2")
    postal_code: Optional[str] = Field(default=None, alias="Code postal", description="Postal code")
    city: Optional[str] = Field(default=None, alias="Commune", description="City")
    phone: Optional[str] = Field(default=None, alias="Téléphone", description="Phone")
    phone_2: Optional[str] = Field(default=None, alias="Téléphone 2", description="Phone 2")
    last_name: Optional[str] = Field(default=None, alias="Nom", description="Last name")
    family_name: Optional[str] = Field(default=None, alias="Nom de famille", description="Family name")
    first_name: Optional[str] = Field(default=None, alias="Prénom", description="First name")

    # 12-21
    insee_city_code: Optional[str] = Field(default=None, alias="Code INSEE Commune", description="INSEE city code")
    country_code: Optional[str] = Field(default=None, alias="Code pays", description="Country code")
    paying_establishment: Optional[str] = Field(default=None, alias="Etablissement payeur", description="Paying establishment")
    social_security_number: Optional[str] = Field(default=None, alias="Numéro de Sécurité Sociale", description="Social security number")
    birth_date: Optional[str] = Field(default=None, alias="Date de naissance", description="Birth date")
    marital_status: Optional[str] = Field(default=None, alias="Situation familiale", description="Marital status")
    nationality_code: Optional[str] = Field(default=None, alias="Nationalité (code)", description="Nationality code")
    civility: Optional[str] = Field(default=None, alias="Civilité", description="Civility")
    contract_start_date: Optional[str] = Field(default=None, alias="Date de début de contrat", description="Contract start date")
    contract_nature: Optional[str] = Field(default=None, alias="Nature du contrat", description="Contract nature")

    # 22-31
    work_modality: Optional[int] = Field(default=None, alias="Modalité d'exercice du travail", description="Work modality")
    profession_entry_date: Optional[str] = Field(default=None, alias="Date d'entrée dans la profession", description="Profession entry date")
    profession_seniority: Optional[str] = Field(default=None, alias="Ancienneté dans la profession", description="Profession seniority")
    company_hire_date: Optional[str] = Field(default=None, nullable=True, alias="Date d'embauche société", description="Company hire date")
    establishment_entry_date: Optional[str] = Field(default=None, alias="Date entrée établissement", description="Establishment entry date")
    establishment_entry_type: Optional[str] = Field(default=None, alias="Type d'entrée établissement", description="Establishment entry type")
    seniority_date: Optional[str] = Field(default=None, alias="Date d'ancienneté", description="Seniority date")
    last_worked_paid_day: Optional[str] = Field(default=None, alias="Dernier jour travaillé et payé", description="Last worked and paid day")
    departure_reason: Optional[str] = Field(default=None, alias="Motif de départ", description="Departure reason")
    conventional_termination_date: Optional[str] = Field(default=None, alias="Date de rupture conventionnelle", description="Conventional termination date")

    # 32-42
    company_departure_date: Optional[str] = Field(default=None, alias="Date de départ société", description="Company departure date")
    establishment_exit_date: Optional[str] = Field(default=None, alias="Date de sortie établissement", description="Establishment exit date")
    employee_base_salary: Optional[float] = Field(default=None, alias="Salaire de base du salarié", description="Employee base salary")
    salary_type: Optional[int] = Field(default=None, alias="Type de salaire", description="Salary type")
    annual_base_salary: Optional[float] = Field(default=None, alias="Salaire de base annuel", description="Annual base salary")
    hourly_wage: Optional[float] = Field(default=None, alias="Salaire horaire du salarié", description="Hourly wage")
    weekly_schedule: Optional[float] = Field(default=None, alias="Horaire hebdomadaire du salarié", description="Weekly schedule of the employee")
    basic_schedule: Optional[str] = Field(default=None, alias="Horaire de base du salarie", description="Employee's basic schedule")
    payment_periodicity: Optional[int] = Field(default=None, alias="Périodicité de paiement", description="Payment periodicity")
    work_time_unit: Optional[str] = Field(default=None, alias="Unité du temps de travail", description="Work time unit")
    activity_modality: Optional[str] = Field(default=None, alias="Modalité de l'activité", description="Activity modality")
    account_number_1: Optional[str] = Field(default="XXXXXXXXXXXXX", alias="Numéro de compte 1", description="Account number 1")
    bank_code_1: Optional[int] = Field(alias="Code Banque", description="Bank code")
    bic_code_1: Optional[str] = Field(default=None, alias="Code BIC 1", description="BIC code 1")

    # 43-46
    account_label_1: Optional[str] = Field(default=None, alias="Libellé du compte 1", description="Account label 1")
    branch_name_1: Optional[str] = Field(default=None, alias="Nom guichet 1", description="Branch name 1")
    branch_code_1: Optional[str] = Field(default="XXXXX", alias="Code guichet 1", description="Branch code 1")
    payment_method: Optional[str] = Field(default=None, alias="Mode de paiement", description="Payment method")
    full_time_equivalent: Optional[str] = Field(default=None, alias="Quotité de travail mensuel", description="Full time equivalent")

    class Config:
        """Schema configuration"""
        populate_by_name = True
        coerce = True


class RegistrationSchema(BrynQPanderaDataFrameModel):
    """Schema for Registration from Sage 100 France."""
    unique_code: Optional[Series[String]] = pa.Field(eq="01", coerce=True, nullable=True, description="01", metadata={"position": 1, "length": 2})
    employee_id: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", metadata={"position": 3, "length": 10})
    reserved_area: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Zone réservée (espaces)", metadata={"position": 13, "length": 1})
    form_of_address: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Civilité", metadata={"position": 14, "length": 1})
    last_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom", metadata={"position": 15, "length": 30})
    maiden_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom de jeune fille", metadata={"position": 45, "length": 30})
    first_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Prénom", metadata={"position": 75, "length": 20})
    other_first_names: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Autres prénoms", metadata={"position": 95, "length": 20})
    address_1: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Adresse 1", metadata={"position": 115, "length": 32})
    address_1_supplement: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Complément d'adresse 1", metadata={"position": 147, "length": 32})
    address_1_city: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Adresse 1 Commune", metadata={"position": 179, "length": 26})
    address_1_postal_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Adresse 1 Code postal", metadata={"position": 205, "length": 5})
    address_1_distribution_office: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Adresse 1 Bureau distributeur", metadata={"position": 210, "length": 26})
    address_1_phone: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Adresse 1 Téléphone", metadata={"position": 236, "length": 15})
    address_2: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Adresse 2", metadata={"position": 251, "length": 32})
    address_2_supplement: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Complément d'adresse 2", metadata={"position": 283, "length": 32})
    address_2_city: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Adresse 2 Commune", metadata={"position": 315, "length": 26})
    address_2_postal_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Adresse 2 Code postal", metadata={"position": 341, "length": 5})
    address_2_distribution_office: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Adresse 2 Bureau distributeur", metadata={"position": 346, "length": 26})
    address_2_phone: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Adresse 2 Téléphone", metadata={"position": 372, "length": 15})
    payslip_address_choice: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Choix adresse sur le bulletin", metadata={"position": 387, "length": 1})
    establishment: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Établissement", metadata={"position": 388, "length": 5})
    auxiliary_account: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Compte auxiliaire", metadata={"position": 393, "length": 13})
    insee_municipality_code: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Code INSEE commune", metadata={"position": 406, "length": 5})
    address_1_country_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Code pays adresse 1", metadata={"position": 411, "length": 3})
    employee_savings_identifier: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Identifiant de l'épargne salariale", metadata={"position": 414, "length": 13})
    employee_savings_identifier_key: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Clé de l'identifiant de l'épargne salariale", metadata={"position": 427, "length": 2})
    tax_resident: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Résident fiscal", metadata={"position": 429, "length": 1})
    subject_to_csg: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Soumis CSG", metadata={"position": 430, "length": 1})
    full_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 80}, description="Nom complet", metadata={"position": 431, "length": 80})
    full_maiden_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 80}, description="Nom de jeune fille complet", metadata={"position": 511, "length": 80})
    email_address: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 128}, description="Adresse courriel", metadata={"position": 591, "length": 128})
    mobile_phone: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Portable", metadata={"position": 719, "length": 15})
    confidentiality: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Confidentialité (0,1,2,3,...,15)", metadata={"position": 734, "length": 2})
    emergency_contact_1_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom Personne 1 à prévenir en cas d'accident", metadata={"position": 736, "length": 30})
    emergency_contact_1_phone: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Tél Personne 1 à prévenir en cas d'accident", metadata={"position": 766, "length": 15})
    emergency_contact_2_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom Personne 2 à prévenir en cas d'accident", metadata={"position": 781, "length": 30})
    emergency_contact_2_phone: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Tél Personne 2 à prévenir en cas d'accident", metadata={"position": 811, "length": 15})
    foreign_distribution_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 50}, description="Code de distribution à l'étranger", metadata={"position": 826, "length": 50})

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "employee_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        coerce = True  # Try to coerce types when possible
        strict = False  # Allow additional columns

class CivilStatusSchema(BrynQPanderaDataFrameModel):
    """Schema for Civil Status from Sage 100 France."""
    unique_code: Optional[Series[String]] = pa.Field(eq="02", coerce=True, nullable=True, description="02", alias="02", metadata={"position": 1, "length": 2})
    employee_id: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", alias="matricule", metadata={"position": 3, "length": 10})
    form_of_address: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Civilité", alias="civilite", metadata={"position": 13, "length": 1})
    last_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom", alias="nom", metadata={"position": 14, "length": 30})
    first_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Prénom", alias="prenom", metadata={"position": 44, "length": 20})
    establishment: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Établissement", alias="établissement", metadata={"position": 64, "length": 5})
    nationality: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Nationalité", alias="nationalite", metadata={"position": 69, "length": 3})
    residence_permit_number: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Carte de séjour N°", alias="carte_de_sejour_n_numero", metadata={"position": 72, "length": 10})
    expiration_date: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date d'expiration", alias="date_d_expiration", metadata={"position": 82, "length": 8})
    issued_by: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Délivrée par", alias="delivree_par", metadata={"position": 90, "length": 20})
    birth_date: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de naissance", alias="date_de_naissance", metadata={"position": 110, "length": 8})
    department: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Département", alias="departement", metadata={"position": 118, "length": 2})
    municipality_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Code commune", alias="code_commune", metadata={"position": 120, "length": 3})
    municipality: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Commune", alias="commune", metadata={"position": 123, "length": 26})
    social_security_number: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Numéro de Sécurité Sociale", alias="numero_de_securite_sociale", metadata={"position": 149, "length": 13})
    social_security_number_key: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Clé du numéro de Sécurité Sociale", alias="cle_du_numero_de_securite_sociale", metadata={"position": 162, "length": 2})
    affiliated_center: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Centre de rattachement", alias="centre_de_rattachement", metadata={"position": 164, "length": 20})
    affiliation_number: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Numéro d'affiliation", alias="numero_d_affiliation", metadata={"position": 184, "length": 20})
    paying_office: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Bureau payeur", alias="bureau_payeur", metadata={"position": 204, "length": 20})
    center_address_street_1: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Adresse du centre Rue 1", alias="adresse_du_centre_rue_1", metadata={"position": 224, "length": 32})
    center_address_street_2: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Adresse du centre Rue 2", alias="adresse_du_centre_rue_2", metadata={"position": 256, "length": 32})
    center_address_city: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Adresse du centre Commune", alias="adresse_du_centre_commune", metadata={"position": 288, "length": 26})
    center_address_postal_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Adresse du centre Code postal", alias="adresse_du_centre_code_postal", metadata={"position": 314, "length": 5})
    center_address_office: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Adresse du centre Bureau", alias="adresse_du_centre_bureau", metadata={"position": 319, "length": 26})
    center_address_phone: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Adresse du centre Téléphone", alias="adresse_du_centre_telephone", metadata={"position": 345, "length": 15})
    establishment_contribution_organization_address_choice: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Choix adresse de l'organisme de cotisa­tion de l'établissement", alias="choix_adresse_de_l_organisme_de_cotisa_tion_de_l_etablissement", metadata={"position": 360, "length": 1})
    marital_status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Situation familiale", alias="situation_familiale", metadata={"position": 361, "length": 1})
    number_of_children: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Nombre d'enfants", alias="nombre_d_enfants", metadata={"position": 362, "length": 2})

    number_of_children_recorded: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Nombre d'enfant renseignés", alias="nombre_d_enfant_renseignes", metadata={"position": 6502, "length": 2})
    unknown: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Non connu", alias="non_connu", metadata={"position": 6504, "length": 1})
    country_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Code Pays", alias="code_pays", metadata={"position": 6505, "length": 3})
    unknown_date: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Date inconnue", alias="date_inconnue", metadata={"position": 6508, "length": 1})
    digital_payslip: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Bulletin dématérialisé", alias="bulletin_dematerialise", metadata={"position": 6509, "length": 1})
    temporary_technical_number: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="N° Technique Temporaire", alias="n_numero_technique_temporaire", metadata={"position": 6510, "length": 40})

    @classmethod
    def get_child_field_metadata(cls, max_children: int = 99) -> dict:
        """
        Returns a dictionary of child field metadata for up to max_children children.
        Each child_X_* field will have its position and length as in the import_civil_status_data field_specs.
        """
        child_metadata = {}
        base_position = 364
        for child_num in range(1, max_children + 1):
            child_base_pos = base_position + ((child_num - 1) * 62)
            child_metadata[f'child_{child_num}_number'] = {"position": child_base_pos, "length": 2}
            child_metadata[f'child_{child_num}_first_name'] = {"position": child_base_pos + 2, "length": 20}
            child_metadata[f'child_{child_num}_last_name'] = {"position": child_base_pos + 22, "length": 30}
            child_metadata[f'child_{child_num}_birth_date'] = {"position": child_base_pos + 52, "length": 8}
            child_metadata[f'child_{child_num}_gender'] = {"position": child_base_pos + 60, "length": 1}
            child_metadata[f'child_{child_num}_dependent'] = {"position": child_base_pos + 61, "length": 1}
        return child_metadata

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "employee_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        coerce = True  # Try to coerce types when possible
        strict = False  # Allow additional columns

class PersonnelRecordTimePageSchema(BrynQPanderaDataFrameModel):
    """Schema for Fiche du personnel - Page Temps from Sage 100 France."""
    unique_code: Optional[Series[String]] = pa.Field(eq="GT", coerce=True, nullable=True, description="GT", metadata={"position": 1, "length": 2})
    employee_id: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, description="Matricule", metadata={"position": 3, "length": 10})
    form_of_address: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Civilité", metadata={"position": 13, "length": 1})
    last_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom", metadata={"position": 14, "length": 30})
    first_name: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Prénom", metadata={"position": 44, "length": 20})
    establishment: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Établissement", metadata={"position": 64, "length": 5})
    last_standard_events_record: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Dernier enregistrement événements stan­dards", metadata={"position": 69, "length": 8})
    last_overtime_record: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Dernier enregistrement Heures supplémen­taires", metadata={"position": 77, "length": 8})
    last_compensatory_rest_record: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Dernier enregistrement Repos compensateur", metadata={"position": 85, "length": 8})
    last_generated_events_record: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Dernier enregistrement événements générés", metadata={"position": 93, "length": 8})
    current_overtime_hours: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Heures supplémentaires en cours", metadata={"position": 101, "length": 10})
    overtime_hours_after_recording: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Heures supplémentaires après enregistre­ment", metadata={"position": 111, "length": 10})
    current_compensatory_rest_balance: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Solde Repos compensateur en cours", metadata={"position": 121, "length": 10})
    compensatory_rest_balance_after_recording: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Solde Repos compensateur après enregistre­ment", metadata={"position": 131, "length": 10})
    compensatory_rest_balance: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Cumul du Repos compensateur", metadata={"position": 141, "length": 10})

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "employee_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        coerce = True  # Try to coerce types when possible
        strict = False  # Allow additional columns

class DadsUSchema(BrynQPanderaDataFrameModel):
    """Schema for DADS-U (Données DADS-U) from Sage 100 France."""
    unique_code: Optional[Series[String]] = pa.Field(eq="DU", coerce=True, nullable=True, description="DU", metadata={"position": 1, "length": 2})
    employee_id: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", metadata={"position": 3, "length": 10})
    first_name_in_use: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Prénom d'usage", metadata={"position": 13, "length": 40})
    surname: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Surnom", metadata={"position": 53, "length": 40})
    profession_entry_date: Optional[Series[DateTime]] = pa.Field(coerce=True, nullable=True, description="Date d'entrée dans la profession", metadata={"position": 93, "length": 8})
    profession_seniority: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Ancienneté dans la profession", metadata={"position": 101, "length": 8})
    average_salary: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Salaire moyen", metadata={"position": 109, "length": 12})
    work_time_unit: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Unité de temps de travail", metadata={"position": 121, "length": 3})
    break_time_unit: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Unité de temps d'arrêt", metadata={"position": 124, "length": 3})
    mandatory_base_regime: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Régime de base obligatoire", metadata={"position": 127, "length": 3})
    professional_status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Statut professionnel", metadata={"position": 130, "length": 3})
    agirc_arrco_category: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Catégoriel AGIRC ARRCO", metadata={"position": 133, "length": 3})
    activity_characteristics: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Caractéristiques de l'activité", metadata={"position": 136, "length": 2})
    reserved_area_1: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 11}, description="Zone réservée (espaces)", metadata={"position": 138, "length": 11})
    workplace_siret: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 14}, description="SIRET du lieu géographique de travail", metadata={"position": 149, "length": 14})
    reserved_area_2: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Zone réservée (espaces)", metadata={"position": 163, "length": 2})
    reserved_area_3: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Zone réservée (espaces)", metadata={"position": 165, "length": 1})
    payroll_offset: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Décalage de paie", metadata={"position": 166, "length": 1})
    foreign_secondment: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Détachement à l'étranger l'activité", metadata={"position": 167, "length": 1})
    holiday_payment_period: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Période de paiement du congé l'activité", metadata={"position": 168, "length": 1})
    unemployment_insurance_beneficiary_code: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Code bénéficiaire assurance chômage", metadata={"position": 169, "length": 1})
    national_compensation_fund_affiliation: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="N° affiliation Fonds Nationaux de Compensation", metadata={"position": 170, "length": 20})
    reserved_area_4: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 833}, description="Zone réservée ; « Espace »", metadata={"position": 190, "length": 833})
    special_situation_change: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Changement de situation particulier", metadata={"position": 1023, "length": 3})
    reserved_area_5: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Zone réservée ; « Espace »", metadata={"position": 1026, "length": 10})
    convention_category: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Catégoriel convention", metadata={"position": 1036, "length": 1})
    reserved_area_6: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Zone réservée ; « Espace »", metadata={"position": 1037, "length": 3})
    cnbf_extension_class: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Classe d'extension CNBF", metadata={"position": 1039, "length": 1})
    reserved_area_7: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Zone réservée ; « 00 »", metadata={"position": 1040, "length": 2})
    reserved_area_8: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 11}, description="Zone réservée ; « Espace »", metadata={"position": 1042, "length": 11})
    reserved_area_9: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 7}, description="Zone réservée ; « Espace »", metadata={"position": 1046, "length": 7})
    work_time_unit_detailed: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Unité de temps de travail détaillée", metadata={"position": 1053, "length": 2})
    reserved_area_10: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Zone réservée ; « Espace »", metadata={"position": 1054, "length": 1})
    paid_holiday_fund: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Caisse de congés payés", metadata={"position": 1055, "length": 1})
    paid_holiday_fund_number: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="N° de caisse congés payés", metadata={"position": 1056, "length": 5})
    aided_employment_agreement_signature_date: Optional[Series[DateTime]] = pa.Field(coerce=True, nullable=True, description="Date de signature convention emploi aidé", metadata={"position": 1061, "length": 8})
    aided_employment_agreement_reference: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Référence convention emploi aidé", metadata={"position": 1069, "length": 10})
    work_exercise_modality: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Modalité d'exercice du travail", metadata={"position": 1079, "length": 2})
    payment_periodicity: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Périodicité de paiement", metadata={"position": 1081, "length": 2})
    reserved_area_11: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Zone réservée ; « Espace »", metadata={"position": 1083, "length": 1})
    work_time_unit_specific: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Unité du temps de travail", metadata={"position": 1084, "length": 1})
    activity_modality: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Modalité de l'activité", metadata={"position": 1085, "length": 2})
    reserved_area_12: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Zone réservée ; « Espace »", metadata={"position": 1087, "length": 1})
    family_relationship: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Lien de parenté", metadata={"position": 1088, "length": 1})
    reserved_area_13: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Zone réservée ; « Espace »", metadata={"position": 1089, "length": 1})
    unemployment_subjection: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Assujettissement chômage", metadata={"position": 1090, "length": 1})
    reserved_area_14: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Zone réservée ; « Espace »", metadata={"position": 1091, "length": 1})
    ags_subjection: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Assujettissement AGS", metadata={"position": 1092, "length": 1})
    reserved_area_15: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Zone réservée ; « Espace »", metadata={"position": 1093, "length": 1})
    exemptions: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Exonérations", metadata={"position": 1094, "length": 1})
    public_employer: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employeur public", metadata={"position": 1095, "length": 1})
    agreement_number: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="N° de convention", metadata={"position": 1096, "length": 10})
    employer_number: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="N° d'employeur", metadata={"position": 1106, "length": 12})
    assignment_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 6}, description="Code affectation", metadata={"position": 1118, "length": 6})
    health_risk: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Risque maladie", metadata={"position": 1124, "length": 3})
    work_accident_risk: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Risque accident du travail", metadata={"position": 1127, "length": 3})
    retirement_risk_employer_part: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Risque vieillesse (part pat.)", metadata={"position": 1130, "length": 3})

    class Config:
        """Schema configuration"""
        coerce = True  # Try to coerce types when possible
        strict = False  # Allow additional columns

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "employee_id"
        foreign_keys = {}
