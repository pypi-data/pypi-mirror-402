import pandera as pa
import pandas as pd
from pandera.typing import Series, String, Float, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class SalaryGetSchema(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating salary data from Sage 100 France T_SAL table.
    This schema ensures that the data follows the expected structure and types.
    """

    # Primary Information
    salary_counter_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Salary counter number", alias="SA_CompteurNumero")
    employee_id: Series[String] = pa.Field(coerce=True, nullable=False, str_length={"max_value": 10}, description="Employee ID", alias="MatriculeSalarie")

    # Personal Information
    civility: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Civility", alias="Civilite")
    last_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 80}, description="Last name", alias="Nom")
    maiden_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 80}, description="Maiden name", alias="NomJeuneFille")
    first_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="First name", alias="Prenom")
    second_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Second name", alias="Prenom2")
    confidentiality: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Confidentiality flag", alias="Confidentialite")
    birth_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Birth date", alias="DateNaissance")
    birth_department: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Birth department", alias="DeptNaissance")
    birth_city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Birth city", alias="CommuneNaissance")
    birth_city_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Birth city code", alias="CodeCommuneNaissance")

    # Address Information - Primary
    street_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Street address line 1", alias="Rue1")
    street_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Street address line 2", alias="Rue2")
    city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="City", alias="Commune")
    distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Distribution office", alias="BureauDistributeur")
    postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Postal code", alias="CodePostal")
    country_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Country code", alias="CodePays")
    phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Phone number", alias="Telephone")

    # Address Information - Secondary
    street_1_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Secondary street address line 1", alias="Rue12")
    street_2_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Secondary street address line 2", alias="Rue22")
    city_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Secondary city", alias="Commune2")
    distribution_office_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Secondary distribution office", alias="BureauDistributeur2")
    postal_code_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Secondary postal code", alias="CodePostal2")
    country_code_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Secondary country code", alias="CodePays2")
    phone_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Secondary phone number", alias="Telephone2")
    address_choice: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Address choice", alias="ChoixSurAdresse")

    # Payment Information
    payment_method: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Payment method", alias="ModeDePaiement")
    payroll_status: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Payroll status", alias="EtatPaie")
    closure: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Closure flag", alias="Cloture")
    payment_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Payment date", alias="DateDePaie")
    closure_date: Series[DateTime] = pa.Field(coerce=True, nullable=True,  description="Closure date", alias="DateDeCloture")
    auxiliary_account: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Auxiliary account", alias="CompteAuxiliaire")

    # Leave Information
    compensatory_rest_accumulation: Series[Float] = pa.Field(coerce=True, nullable=True, description="Compensatory rest accumulation", alias="CumulsReposCompensateur")
    remaining_to_take: Series[Float] = pa.Field(coerce=True, nullable=True, description="Remaining to take", alias="ResteAPrendre")
    previous_acquired: Series[Float] = pa.Field(coerce=True, nullable=True, description="Previous acquired", alias="AcquisPrecedent")
    current_acquired: Series[Float] = pa.Field(coerce=True, nullable=True, description="Current acquired", alias="AcquisEnCours")
    previous_gross_accumulation: Series[Float] = pa.Field(coerce=True, nullable=True, description="Previous gross accumulation", alias="CumulsBrutPrecedent")
    previous_gross_cp_bis: Series[Float] = pa.Field(coerce=True, nullable=True, description="Previous gross CP bis", alias="BrutCPPrecedentBis")

    # Seniority Information
    company_seniority_months: Series[Float] = pa.Field(coerce=True, nullable=True, description="Company seniority in months", alias="MoisAncienneteSociete")
    establishment_seniority_months: Series[Float] = pa.Field(coerce=True, nullable=True, description="Establishment seniority in months", alias="MoisAncienneteEtablissement")
    position_seniority_months: Series[Float] = pa.Field(coerce=True, nullable=True, description="Position seniority in months", alias="MoisAnciennetePoste")
    branch_sector_seniority_months: Series[Float] = pa.Field(coerce=True, nullable=True, description="Branch/sector seniority in months", alias="MoisAncienBrancheOuSecteur")
    group_seniority_months: Series[Float] = pa.Field(coerce=True, nullable=True, description="Group seniority in months", alias="MoisAncienneteGroupe")
    seniority_precision: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 255}, description="Seniority precision", alias="PrecisionAnciennete")

    # Contact Information
    email: Series[String] = pa.Field(coerce=True, nullable=True, regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', str_length={"max_value": 128}, description="Email address", alias="EMail")
    mobile_number: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Mobile number", alias="NumeroDePortable")
    professional_phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Professional phone", alias="TelephoneProfessionnel")
    professional_mobile: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Professional mobile", alias="TelephPortableProfessionnel")
    professional_fax: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Professional fax", alias="FaxProfessionnel")
    professional_email: Series[String] = pa.Field(coerce=True, nullable=True, regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', str_length={"max_value": 128}, description="Professional email", alias="AdresseMelProfessionnelle")

    # Emergency Contacts
    emergency_contact_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Emergency contact 1", alias="APrevenirPersonne01")
    emergency_phone_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Emergency phone 1", alias="APrevenirTelephone01")
    emergency_contact_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Emergency contact 2", alias="APrevenirPersonne02")
    emergency_phone_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Emergency phone 2", alias="APrevenirTelephone02")

    # Additional Information
    comment_1: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 60}, description="Comment 1", alias="Commentaire1")
    comment_2: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 60}, description="Comment 2", alias="Commentaire2")
    comment_3: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 60}, description="Comment 3", alias="Commentaire3")
    memo: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 254}, description="Memo", alias="Memo")
    general_info_flag: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="General information flag", alias="FlagInfosGenerales")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "salary_counter_number"
        foreign_keys = {
            "employee_id": {
                "parent_schema": "EmployeeSchema",
                "parent_column": "employee_id",
                "cardinality": "N:1"
            }
        }

    class Config:
        """Schema configuration"""
        strict = False  # Allow additional columns as there are many fields
        coerce = True  # Try to coerce types when possible


# Auto-generated Pandera schemas from Sage 100 France
# File: salary.py

import pandas as pd
import pandera as pa
from pandera.typing import Series, String, Float
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class SalarySchema(BrynQPanderaDataFrameModel):
    """Schema for Salary from Sage 100 France."""
    field_05: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="05", alias="05")
    employee_id: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", alias="matricule")
    form_of_address: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Civilité", alias="civilite")
    last_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom", alias="nom")
    first_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Prénom", alias="prenom")
    establishment: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Établissement", alias="établissement")
    payslip_template: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 4}, description="Bulletin modèle", alias="bulletin_modele")
    salary_type: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Type de salaire", alias="type_de_salaire")
    base_salary: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Salaire de base", alias="salaire_de_base")
    hourly_wage: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Salaire horaire", alias="salaire_horaire")
    rate_type: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Type de taux", alias="type_de_taux")
    schedule: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Horaire", alias="horaire")
    weekly_schedule: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Horaire hebdomadaire", alias="horaire_hebdomadaire")
    annual_base_salary: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Salaire de base annuel", alias="salaire_de_base_annuel")
    number_of_months: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Nombre de mois", alias="nombre_de_mois")
    last_pay_period_start: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Début de la dernière période de paie", alias="debut_de_la_derniere_periode_de_paie")
    last_pay_period_end: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Fin de la dernière période de paie", alias="fin_de_la_derniere_periode_de_paie")
    last_closure_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de dernière clôture", alias="date_de_derniere_cloture")
    systematic_regularization: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Régularisation systématique", alias="regularisation_systematique")
    number_of_employers: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Nombre d'employeurs", alias="nombre_d_employeurs")
    employer_1_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Employeur 1 Numéro", alias="employeur_1_numero")
    employer_1_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 1 Date de début", alias="employeur_1_date_de_debut")
    employer_1_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 1 Date de fin", alias="employeur_1_date_de_fin")
    employer_1_company_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Employeur 1 Raison sociale", alias="employeur_1_raison_sociale")
    employer_1_gross_amount: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Employeur 1 Montant brut", alias="employeur_1_montant_brut")
    employer_1_address: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 1 Adresse", alias="employeur_1_adresse")
    employer_1_address_supplement: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 1 Complément d'adresse", alias="employeur_1_complement_d_adresse")
    employer_1_city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 1 Commune", alias="employeur_1_commune")
    employer_1_postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Employeur 1 Code postal", alias="employeur_1_code_postal")
    employer_1_distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 1 Bureau distributeur", alias="employeur_1_bureau_distributeur")
    employer_1_phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Employeur 1 Téléphone", alias="employeur_1_telephone")
    employer_2_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Employeur 2 Numéro", alias="employeur_2_numero")
    employer_2_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 2 Date de début", alias="employeur_2_date_de_debut")
    employer_2_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 2 Date de fin", alias="employeur_2_date_de_fin")
    employer_2_company_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Employeur 2 Raison sociale", alias="employeur_2_raison_sociale")
    employer_2_gross_amount: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Employeur 2 Montant brut", alias="employeur_2_montant_brut")
    employer_2_address: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 2 Adresse", alias="employeur_2_adresse")
    employer_2_address_supplement: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 2 Complément d'adresse", alias="employeur_2_complement_d_adresse")
    employer_2_city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 2 Commune", alias="employeur_2_commune")
    employer_2_postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Employeur 2 Code postal", alias="employeur_2_code_postal")
    employer_2_distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 2 Bureau distributeur", alias="employeur_2_bureau_distributeur")
    employer_2_phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Employeur 2 Téléphone", alias="employeur_2_telephone")
    employer_3_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Employeur 3 Numéro", alias="employeur_3_numero")
    employer_3_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 3 Date de début", alias="employeur_3_date_de_debut")
    employer_3_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 3 Date de fin", alias="employeur_3_date_de_fin")
    employer_3_company_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Employeur 3 Raison sociale", alias="employeur_3_raison_sociale")
    employer_3_gross_amount: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Employeur 3 Montant brut", alias="employeur_3_montant_brut")
    employer_3_address: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 3 Adresse", alias="employeur_3_adresse")
    employer_3_address_supplement: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 3 Complément d'adresse", alias="employeur_3_complement_d_adresse")
    employer_3_city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 3 Commune", alias="employeur_3_commune")
    employer_3_postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Employeur 3 Code postal", alias="employeur_3_code_postal")
    employer_3_distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 3 Bureau distributeur", alias="employeur_3_bureau_distributeur")
    employer_3_phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Employeur 3 Téléphone", alias="employeur_3_telephone")
    employer_4_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Employeur 4 Numéro", alias="employeur_4_numero")
    employer_4_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 4 Date de début", alias="employeur_4_date_de_debut")
    employer_4_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 4 Date de fin", alias="employeur_4_date_de_fin")
    employer_4_company_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Employeur 4 Raison sociale", alias="employeur_4_raison_sociale")
    employer_4_gross_amount: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Employeur 4 Montant brut", alias="employeur_4_montant_brut")
    employer_4_address: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 4 Adresse", alias="employeur_4_adresse")
    employer_4_address_supplement: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 4 Complément d'adresse", alias="employeur_4_complement_d_adresse")
    employer_4_city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 4 Commune", alias="employeur_4_commune")
    employer_4_postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Employeur 4 Code postal", alias="employeur_4_code_postal")
    employer_4_distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 4 Bureau distributeur", alias="employeur_4_bureau_distributeur")
    employer_4_phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Employeur 4 Téléphone", alias="employeur_4_telephone")
    employer_5_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Employeur 5 Numéro", alias="employeur_5_numero")
    employer_5_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 5 Date de début", alias="employeur_5_date_de_debut")
    employer_5_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Employeur 5 Date de fin", alias="employeur_5_date_de_fin")
    employer_5_company_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 40}, description="Employeur 5 Raison sociale", alias="employeur_5_raison_sociale")
    employer_5_gross_amount: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Employeur 5 Montant brut", alias="employeur_5_montant_brut")
    employer_5_address: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 5 Adresse", alias="employeur_5_adresse")
    employer_5_address_supplement: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 32}, description="Employeur 5 Complément d'adresse", alias="employeur_5_complement_d_adresse")
    employer_5_city: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 5 Commune", alias="employeur_5_commune")
    employer_5_postal_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Employeur 5 Code postal", alias="employeur_5_code_postal")
    employer_5_distribution_office: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 26}, description="Employeur 5 Bureau distributeur", alias="employeur_5_bureau_distributeur")
    employer_5_phone: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 15}, description="Employeur 5 Téléphone", alias="employeur_5_telephone")
    last_record: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Dernier enregistrement (Feuille de temps)", alias="dernier_enregistrement")
    last_record: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Dernier enregistrement (Heures supplémen­taires)", alias="dernier_enregistrement")
    last_record: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Dernier enregistrement (Repos compensateur)", alias="dernier_enregistrement")
    unknown_1: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Non connu (multi-employeurs) – 1", alias="non_connu_1")
    piece_rate_paid: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Rémunéré à la tâche – 1", alias="remunere_a_la_tache_1")
    number_of_multi_employers_recorded: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Nombre de multi-employeurs renseignés", alias="nombre_de_multi_employeurs_renseignes")
    reserved_area: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 6}, description="Zone réservée (espaces)", alias="zone_reservee")
    full_time_equivalent: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 4}, description="Équivalent temps plein", alias="équivalent_temps_plein")
    reserved_area: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Zone réservée (00)", alias="zone_reservee")
    payment_frequency: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Périodicité de paiement", alias="periodicite_de_paiement")
    work_time_unit: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Unité du temps de travail", alias="unite_du_temps_de_travail")
    activity_modality: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Modalité de l'activité", alias="modalite_de_l_activite")
    category: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Catégorie", alias="categorie")
    monthly_work_percentage: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Quotité de travail mensuelle", alias="quotite_de_travail_mensuelle")
    cice_excluded: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Exclus du CICE", alias="exclus_du_cice")
    dsn_system_excluded: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Exclus du dispositif DSN", alias="exclus_du_dispositif_dsn")
    dsn_exclusion_reason: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Motif d'exclusion DSN", alias="motif_d_exclusion_dsn")
    prepayment_type: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Type de prépaiement : 0 = Etablissement, 1 = Catégorie", alias="type_de_prepaiement")


class WithholdingTaxSchema(BrynQPanderaDataFrameModel):
    """Schema for Withholding Tax from Sage 100 France."""
    ip: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="IP", alias="ip")
    employee_id: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", alias="matricule")
    tax_scale_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Code du Barème", alias="code_du_bareme")
    nominal_rate: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 8}, description="Taux nominatif", alias="taux_nominatif")
    no_rate: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Pas de taux", alias="pas_de_taux")
    validity_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de validité", alias="date_de_validite")
    crm_identifier: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Identifiant CRM", alias="identifiant_crm")


class TaxSchema(BrynQPanderaDataFrameModel):
    """Schema for Tax from Sage 100 France."""
    field_09: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="09", alias="09")
    employee_id: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", alias="matricule")
    form_of_address: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Civilité", alias="civilite")
    last_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom", alias="nom")
    first_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Prénom", alias="prenom")
    establishment: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Établissement", alias="établissement")
    professional_expenses: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Frais professionnels", alias="frais_professionnels")
    flat_rate_allowance: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Allocation forfaitaire", alias="allocation_forfaitaire")
    expense_on_receipts: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Frais sur justificatifs", alias="frais_sur_justificatifs")
    employer_coverage: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Prise en charge par l'employeur", alias="prise_en_charge_par_l_employeur")
    advance_reimbursement: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Remboursement par avance", alias="remboursement_par_avance")
    flat_rate_deduction_reduction_rate: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 7}, description="Taux de l'abattement pour la déduction forfaitaire", alias="taux_de_l_abattement_pour_la_deduction_forfaitaire")
    supplementary_deduction_option: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Option de déduction supplémentaire", alias="option_de_deduction_supplementaire")
    payroll_taxes_agglomerating_establishment: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 6}, description="Taxes sur les salaires, établissement agglomérant", alias="taxes_sur_les_salaires_etablissement_agglomerant")
    other_reimbursements: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Autres remboursements", alias="autres_remboursements")
    pas_rate_type: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Type de taux PAS", alias="type_de_taux_pas")
    calculated_pas_validity: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Validité calculée PAS", alias="validite_calculee_pas")


class LeaveSchema(BrynQPanderaDataFrameModel):
    """Schema for Leave from Sage 100 France."""
    field_06: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="06", alias="06")
    employee_id: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", alias="matricule")
    form_of_address: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Civilité", alias="civilite")
    last_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Nom", alias="nom")
    first_name: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Prénom", alias="prenom")
    establishment: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Établissement", alias="établissement")
    compensatory_rest_balance: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Cumul repos compensateur", alias="cumul_repos_compensateur")
    leave_remaining_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre année précédente (Jours)", alias="conges_restant_a_prendre_annee_precedente")
    leave_earned_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis année en cours (Jours)", alias="conges_acquis_annee_en_cours")
    leave_earned_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis année précédente (Jours)", alias="conges_acquis_annee_precedente")
    supplementary_entitlement: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Droit supplémentaire", alias="droit_supplementaire")
    number_of_saturdays_taken: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Nombre de samedis pris", alias="nombre_de_samedis_pris")
    gross_leave_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Brut congés N-1", alias="brut_conges_n_1")
    gross_leave_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Brut congés N", alias="brut_conges_n")
    leave_closure_month: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 2}, description="Mois de clôture des congés", alias="mois_de_cloture_des_conges")
    leave_1_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de début congés 1", alias="date_de_debut_conges_1")
    leave_1_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de fin congés 1", alias="date_de_fin_conges_1")
    leave_2_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de début congés 2", alias="date_de_debut_conges_2")
    leave_2_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de fin congés 2", alias="date_de_fin_conges_2")
    leave_3_start_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de début congés 3", alias="date_de_debut_conges_3")
    leave_3_end_date: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de fin congés 3", alias="date_de_fin_conges_3")
    company_seniority: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 8}, description="Ancienneté société (mois)", alias="anciennete_societe")
    establishment_seniority: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 8}, description="Ancienneté établissement (mois)", alias="anciennete_etablissement")
    position_seniority: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 8}, description="Ancienneté poste (mois)", alias="anciennete_poste")
    annual_overtime_total: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Cumul annuel HS (**)", alias="cumul_annuel_hs")
    compensatory_rest_balance_after_recording: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Solde des heures de RC après enregistrement (**)", alias="solde_des_heures_de_rc_apres_enregistrement")
    compensatory_rest_balance_current_period: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Solde des heures de RC sur la période en cours(**)", alias="solde_des_heures_de_rc_sur_la_periode_en_cours")
    current_overtime_hours_quota: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Contingent d'heures supplémentaires en cours (**)", alias="contingent_d_heures_supplementaires_en_cours")
    leave_reset_on_employee_departure: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 1}, description="Remise à zéro des congés au départ du salarié", alias="remise_a_zero_des_conges_au_depart_du_salarie")
    statutory_leave_earned_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis légal N", alias="conges_acquis_legal_n")
    statutory_leave_earned_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis légal N-1", alias="conges_acquis_legal_n_1")
    statutory_leave_earned_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis légal N-2", alias="conges_acquis_legal_n_2")
    split_leave_earned_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis fractionnement N", alias="conges_acquis_fractionnement_n")
    split_leave_earned_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis fractionnement N-1", alias="conges_acquis_fractionnement_n_1")
    split_leave_earned_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis fractionnement N-2", alias="conges_acquis_fractionnement_n_2")
    seniority_leave_earned_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis ancienneté N", alias="conges_acquis_anciennete_n")
    seniority_leave_earned_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis ancienneté N-1", alias="conges_acquis_anciennete_n_1")
    seniority_leave_earned_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis ancienneté N-2", alias="conges_acquis_anciennete_n_2")
    supplementary_leave_earned_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis supplémentaire N", alias="conges_acquis_supplementaire_n")
    supplementary_leave_earned_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis supplémentaire N-1", alias="conges_acquis_supplementaire_n_1")
    supplementary_leave_earned_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis supplémentaire N-2", alias="conges_acquis_supplementaire_n_2")
    statutory_leave_remaining_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre légal N", alias="conges_restant_a_prendre_legal_n")
    statutory_leave_remaining_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre légal N-1", alias="conges_restant_a_prendre_legal_n_1")
    statutory_leave_remaining_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre légal N-2", alias="conges_restant_a_prendre_legal_n_2")
    split_leave_remaining_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre fractionnement N", alias="conges_restant_a_prendre_fractionnement_n")
    split_leave_remaining_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre fractionnement N-1", alias="conges_restant_a_prendre_fractionnement_n_1")
    split_leave_remaining_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre fractionnement N-2", alias="conges_restant_a_prendre_fractionnement_n_2")
    seniority_leave_remaining_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre ancienneté N", alias="conges_restant_a_prendre_anciennete_n")
    seniority_leave_remaining_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre ancienneté N-1", alias="conges_restant_a_prendre_anciennete_n_1")
    seniority_leave_remaining_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre ancienneté N-2", alias="conges_restant_a_prendre_anciennete_n_2")
    supplementary_leave_remaining_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre supplémentaire N", alias="conges_restant_a_prendre_supplementaire_n")
    supplementary_leave_remaining_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre supplémentaire N-1", alias="conges_restant_a_prendre_supplementaire_n_1")
    supplementary_leave_remaining_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre supplémentaire N-2", alias="conges_restant_a_prendre_supplementaire_n_2")
    total_leave_earned_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis total N-2", alias="conges_acquis_total_n_2")
    total_leave_remaining_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre total N", alias="conges_restant_a_prendre_total_n")
    total_leave_remaining_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés restant à prendre total N-2", alias="conges_restant_a_prendre_total_n_2")
    total_leave_taken_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés pris total N", alias="conges_pris_total_n")
    total_leave_taken_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés pris total N-1", alias="conges_pris_total_n_1")
    total_leave_taken_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés pris total N-2", alias="conges_pris_total_n_2")
    gross_leave_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Brut congés N-2", alias="brut_conges_n_2")
    leave_duration_v7: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Durée de prise des congés, déjà le cas en version 7.00", alias="duree_de_prise_des_conges_deja_le_cas_en_version_7_00")
    leave_start_v7: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Début de prise des congés, déjà le cas en version 7.00", alias="debut_de_prise_des_conges_deja_le_cas_en_version_7_00")
    non_occupational_illness_leave_earned_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis maladie non pro N", alias="conges_acquis_maladie_non_pro_n")
    non_occupational_illness_leave_earned_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis maladie non pro N-1", alias="conges_acquis_maladie_non_pro_n_1")
    non_occupational_illness_leave_earned_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés acquis maladie non pro N-2", alias="conges_acquis_maladie_non_pro_n_2")
    non_occupational_illness_leave_remaining_current_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés reste à prendre maladie non pro N", alias="conges_reste_a_prendre_maladie_non_pro_n")
    non_occupational_illness_leave_remaining_previous_year: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés reste à prendre maladie non pro N-1", alias="conges_reste_a_prendre_maladie_non_pro_n_1")
    non_occupational_illness_leave_remaining_two_years_ago: Series[Float] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 12}, description="Congés reste à prendre maladie non pro N-2", alias="conges_reste_a_prendre_maladie_non_pro_n_2")
    expiration_date_current_year: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date d'expiration N", alias="date_d_expiration_n")
    expiration_date_previous_year: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date d'expiration N-1", alias="date_d_expiration_n_1")
    expiration_date_two_years_ago: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date d'expiration N-2", alias="date_d_expiration_n_2")
