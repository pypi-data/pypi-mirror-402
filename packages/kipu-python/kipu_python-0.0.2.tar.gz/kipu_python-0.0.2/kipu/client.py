"""
Main Kipu API Client
Implements all available API endpoints with proper typing and documentation
"""

from typing import Any, Dict, Optional, Union

import pandas as pd

from .base_client import BaseKipuClient
from .flattener import JsonFlattener


class KipuClient(BaseKipuClient):
    def __init__(
        self,
        access_id: str,
        secret_key: str,
        app_id: str,
        base_url: str = "https://api.kipuapi.com",
        version: int = 3,
        timeout: int = 30,
        auto_flatten: bool = True,
    ):
        """
        Initialize Kipu API client

        Args:
            access_id: Your access ID provided by Kipu
            secret_key: Your secret key provided by Kipu
            app_id: Your app ID provided by Kipu
            base_url: Base URL for Kipu API
            timeout: Request timeout in seconds
            auto_flatten: Automatically flatten nested JSON responses to DataFrame
        """
        super().__init__(access_id, secret_key, app_id, base_url, version, timeout)
        self.auto_flatten = auto_flatten
        self.flattener = JsonFlattener()

    async def _process_response(
        self, response_data: Dict[str, Any], flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Process API response, optionally flattening to DataFrame

        Args:
            response_data: Raw API response
            flatten: Override auto_flatten setting

        Returns:
            Processed response (dict or DataFrame)
        """
        should_flatten = flatten if flatten is not None else self.auto_flatten

        if should_flatten and isinstance(response_data, list):
            # Flatten list of records to DataFrame
            return await self.flattener.flatten_json_df(response_data)
        elif should_flatten and isinstance(response_data, dict):
            # Flatten single record to DataFrame
            flattened = self.flattener.flatten_json(response_data)
            return pd.DataFrame(flattened)
        else:
            return response_data

    # =============================================================================
    # PATIENT ENDPOINTS
    # =============================================================================

    async def get_patients_census(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patients from a census of the database

        Args:
            params: Query parameters (phi_level, page, per, start_date, end_date, etc.)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patients/census", params)
        return await self._process_response(response, flatten)

    async def get_patient(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch a Patient Record

        Args:
            patient_id: Patient ID
            params: Query parameters (include_ids, insurance_detail, etc.)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}", params)
        return await self._process_response(response, flatten)

    async def create_patient(
        self,
        patient_data: Dict[str, Any],
        files: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Create a new patient

        Args:
            patient_data: Patient data including document[recipient_id] and document[data]
            files: File attachments (document[attachments_attributes])
            flatten: Override auto_flatten setting
        """
        response = await self.post("/api/patients", patient_data, files)
        return await self._process_response(response, flatten)

    async def update_patient(
        self,
        patient_id: str,
        patient_data: Dict[str, Any],
        files: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Update a patient

        Args:
            patient_id: Patient ID
            patient_data: Updated patient data
            files: File attachments
            flatten: Override auto_flatten setting
        """
        response = await self.patch(f"/api/patients/{patient_id}", patient_data, files)
        return await self._process_response(response, flatten)

    async def get_patients_admissions(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List admissions within a date range

        Args:
            params: Query parameters (start_date, end_date, location_id, etc.)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patients/admissions", params)
        return await self._process_response(response, flatten)

    async def get_patients_latest(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List patients with updated_at within a date range

        Args:
            params: Query parameters (start_date, end_date, etc.)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patients/latest", params)
        return await self._process_response(response, flatten)

    async def get_patients_occupancy(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Get occupancy information

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patients/occupancy", params)
        return await self._process_response(response, flatten)

    async def get_patients_care_teams(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patients' care teams

        Args:
            params: Query parameters (page, per)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patients/care_teams", params)
        return await self._process_response(response, flatten)

    async def get_patient_care_team(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List a patient's care team

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/care_team", params)
        return await self._process_response(response, flatten)

    async def get_patient_diagnosis_history(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List a patient's diagnosis history

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(
            f"/api/patients/{patient_id}/diagnosis_history", params
        )
        return await self._process_response(response, flatten)

    async def get_patient_program_history(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List a patient's program history

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/program_history", params)
        return await self._process_response(response, flatten)

    async def get_patients_processes(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patient processes

        Args:
            params: Query parameters (process_details)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patients/processes", params)
        return await self._process_response(response, flatten)

    async def get_vaults_patients(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Lists all soft-deleted patients

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/vaults/patients", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # APPOINTMENT ENDPOINTS
    # =============================================================================

    async def get_appointments(
        self,
        appointment_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch an Appointment Record

        Args:
            appointment_id: Appointment ID
            params: Query parameters (days)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/appointments/{appointment_id}", params)
        return await self._process_response(response, flatten)

    async def get_patient_appointments(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all appointments scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters (days)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/appointments", params)
        return await self._process_response(response, flatten)

    async def get_provider_appointments(
        self,
        provider_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all appointments scoped to a given provider

        Args:
            provider_id: Provider ID
            params: Query parameters (days)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/providers/{provider_id}/appointments", params)
        return await self._process_response(response, flatten)

    async def get_user_appointments(
        self,
        user_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all appointments scoped to a given user

        Args:
            user_id: User ID
            params: Query parameters (days)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/users/{user_id}/appointments", params)
        return await self._process_response(response, flatten)

    async def get_scheduler_appointments(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all appointments

        Args:
            params: Query parameters (start_date, end_date)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/scheduler/appointments", params)
        return await self._process_response(response, flatten)

    async def get_scheduler_appointment(
        self,
        appointment_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch an appointment

        Args:
            appointment_id: Appointment ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(
            f"/api/scheduler/appointments/{appointment_id}", params
        )
        return await self._process_response(response, flatten)

    async def get_scheduler_appointment_types(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all appointment types

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/scheduler/appointment_types", params)
        return await self._process_response(response, flatten)

    async def get_scheduler_appointment_statuses(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all appointment statuses

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/scheduler/appointment_statuses", params)
        return await self._process_response(response, flatten)

    async def get_scheduler_resources(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all resources

        Args:
            params: Query parameters (enabled, category_type)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/scheduler/resources", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # MEDICAL RECORDS ENDPOINTS
    # =============================================================================

    async def get_patient_vital_signs(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all vital signs scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters (created_at_start_date, created_at_end_date, etc.)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/vital_signs", params)
        return await self._process_response(response, flatten)

    async def create_patient_vital_signs(
        self,
        patient_id: str,
        vital_signs_data: Dict[str, Any],
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Create a new vital sign for a patient

        Args:
            patient_id: Patient ID
            vital_signs_data: Vital signs data
            flatten: Override auto_flatten setting
        """
        response = await self.post(
            f"/api/patients/{patient_id}/vital_signs", vital_signs_data
        )
        return await self._process_response(response, flatten)

    async def get_vital_signs(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all vital signs

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/vital_signs", params)
        return await self._process_response(response, flatten)

    async def get_patient_allergies(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List allergies scoped to a patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/allergies", params)
        return await self._process_response(response, flatten)

    async def get_allergies(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all allergies

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/allergies", params)
        return await self._process_response(response, flatten)

    async def get_allergens(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all allergens

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/allergens", params)
        return await self._process_response(response, flatten)

    async def get_patient_cows(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Cows scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters (created_at_start_date, etc.)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/cows", params)
        return await self._process_response(response, flatten)

    async def get_cows(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Cows

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/cows", params)
        return await self._process_response(response, flatten)

    async def get_patient_ciwa_ars(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all CiwaArs scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/ciwa_ars", params)
        return await self._process_response(response, flatten)

    async def get_ciwa_ars(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all CiwaArs

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/ciwa_ars", params)
        return await self._process_response(response, flatten)

    async def get_patient_ciwa_bs(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all CiwaBs scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/ciwa_bs", params)
        return await self._process_response(response, flatten)

    async def get_ciwa_bs(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all CiwaBs

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/ciwa_bs", params)
        return await self._process_response(response, flatten)

    async def get_patient_glucose_logs(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Glucose Logs scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters (created_at_start_date, evaluation_start_date, etc.)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/glucose_logs", params)
        return await self._process_response(response, flatten)

    async def get_glucose_logs(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all GlucoseLogs

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/glucose_logs", params)
        return await self._process_response(response, flatten)

    async def get_patient_orthostatic_vital_signs(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Orthostatic vital signs scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(
            f"/api/patients/{patient_id}/orthostatic_vital_signs", params
        )
        return await self._process_response(response, flatten)

    async def get_orthostatic_vital_signs(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all orthostatic vital signs

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/orthostatic_vital_signs", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # EVALUATION ENDPOINTS
    # =============================================================================

    async def get_evaluations(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Evaluations

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/evaluations", params)
        return await self._process_response(response, flatten)

    async def get_evaluation(
        self,
        evaluation_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch Details for a Evaluation

        Args:
            evaluation_id: Evaluation ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/evaluations/{evaluation_id}", params)
        return await self._process_response(response, flatten)

    async def get_patient_evaluations(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Patient Evaluations

        Args:
            params: Query parameters (evaluation_content, patient_process_id)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patient_evaluations", params)
        return await self._process_response(response, flatten)

    async def get_patient_evaluation(
        self,
        patient_evaluation_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch Details for a Patient Evaluation

        Args:
            patient_evaluation_id: Patient Evaluation ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(
            f"/api/patient_evaluations/{patient_evaluation_id}", params
        )
        return await self._process_response(response, flatten)

    async def get_patient_patient_evaluations(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Patient Evaluations scoped to a patient

        Args:
            patient_id: Patient ID
            params: Query parameters (evaluation_content, patient_process_id)
            flatten: Override auto_flatten setting
        """
        response = await self.get(
            f"/api/patients/{patient_id}/patient_evaluations", params
        )
        return await self._process_response(response, flatten)

    async def create_patient_evaluation(
        self,
        patient_id: str,
        evaluation_data: Dict[str, Any],
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Create a new patient evaluation

        Args:
            patient_id: Patient ID
            evaluation_data: Evaluation data
            flatten: Override auto_flatten setting
        """
        response = await self.post(
            f"/api/patients/{patient_id}/patient_evaluations", evaluation_data
        )
        return await self._process_response(response, flatten)

    # =============================================================================
    # USER AND PROVIDER ENDPOINTS
    # =============================================================================

    async def get_users(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Users

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/users", params)
        return await self._process_response(response, flatten)

    async def get_user(
        self,
        user_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch a User Record

        Args:
            user_id: User ID
            params: Query parameters (include_restrictions)
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/users/{user_id}", params)
        return await self._process_response(response, flatten)

    async def get_user_roles(
        self,
        user_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all roles scoped to a given user

        Args:
            user_id: User ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/users/{user_id}/roles", params)
        return await self._process_response(response, flatten)

    async def get_providers(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Providers

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/providers", params)
        return await self._process_response(response, flatten)

    async def get_provider(
        self,
        provider_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch a Provider Record

        Args:
            provider_id: Provider ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/providers/{provider_id}", params)
        return await self._process_response(response, flatten)

    async def get_provider_roles(
        self,
        provider_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all roles scoped to a given provider

        Args:
            provider_id: Provider ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/providers/{provider_id}/roles", params)
        return await self._process_response(response, flatten)

    async def get_roles(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Roles

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/roles", params)
        return await self._process_response(response, flatten)

    async def get_role_users(
        self,
        role_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all users scoped to a given role

        Args:
            role_id: Role ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/roles/{role_id}/users", params)
        return await self._process_response(response, flatten)

    async def get_user_titles(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List user titles

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/user_titles", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # CONTACT ENDPOINTS
    # =============================================================================

    async def get_contacts(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all contacts

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/contacts", params)
        return await self._process_response(response, flatten)

    async def get_contact(
        self,
        contact_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetches a contact

        Args:
            contact_id: Contact ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/contacts/{contact_id}", params)
        return await self._process_response(response, flatten)

    async def create_contact(
        self, contact_data: Dict[str, Any], flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Create a new contact

        Args:
            contact_data: Contact data
            flatten: Override auto_flatten setting
        """
        response = await self.post("/api/contacts", contact_data)
        return await self._process_response(response, flatten)

    async def update_contact(
        self,
        contact_id: str,
        contact_data: Dict[str, Any],
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Update a contact

        Args:
            contact_id: Contact ID
            contact_data: Updated contact data
            flatten: Override auto_flatten setting
        """
        response = await self.patch(f"/api/contacts/{contact_id}", contact_data)
        return await self._process_response(response, flatten)

    async def get_contact_types(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all contact types

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/contact_types", params)
        return await self._process_response(response, flatten)

    async def get_referrers(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all referrers

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/contacts/referrers", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # INSURANCE ENDPOINTS
    # =============================================================================

    async def get_insurances_latest(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List insurances with updated_at within a date range

        Args:
            params: Query parameters (start_date, end_date)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/insurances/latest", params)
        return await self._process_response(response, flatten)

    async def update_patient_insurance(
        self,
        patient_id: str,
        insurance_id: str,
        insurance_data: Dict[str, Any],
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Update an insurance

        Args:
            patient_id: Patient ID
            insurance_id: Insurance ID
            insurance_data: Updated insurance data
            flatten: Override auto_flatten setting
        """
        response = await self.patch(
            f"/api/patients/{patient_id}/insurances/{insurance_id}", insurance_data
        )
        return await self._process_response(response, flatten)

    # =============================================================================
    # GROUP SESSION ENDPOINTS
    # =============================================================================

    async def get_group_sessions(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all group sessions

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/group_sessions", params)
        return await self._process_response(response, flatten)

    async def get_group_session(
        self,
        group_session_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetches a group session

        Args:
            group_session_id: Group session ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/group_sessions/{group_session_id}", params)
        return await self._process_response(response, flatten)

    async def get_patient_group_sessions(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all group sessions scoped to a given patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/group_sessions", params)
        return await self._process_response(response, flatten)

    async def get_patient_group_session(
        self,
        patient_id: str,
        group_session_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetches group session of the given patient

        Args:
            patient_id: Patient ID
            group_session_id: Group session ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(
            f"/api/patients/{patient_id}/group_sessions/{group_session_id}", params
        )
        return await self._process_response(response, flatten)

    # =============================================================================
    # CONSENT FORM ENDPOINTS
    # =============================================================================

    async def get_consent_forms(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Consent Forms

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/consent_forms", params)
        return await self._process_response(response, flatten)

    async def get_consent_form_records(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Consent Form Records

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/consent_form_records", params)
        return await self._process_response(response, flatten)

    async def get_consent_form_record(
        self,
        record_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch Details for a Consent Form Record

        Args:
            record_id: Record ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/consent_form_records/{record_id}", params)
        return await self._process_response(response, flatten)

    async def get_patient_consent_form_records(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Consent Form Records for a patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(
            f"/api/patients/{patient_id}/consent_form_records", params
        )
        return await self._process_response(response, flatten)

    # =============================================================================
    # PATIENT DIET ENDPOINTS
    # =============================================================================

    async def get_patient_diets(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patient diets

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patient_diets", params)
        return await self._process_response(response, flatten)

    async def get_patient_patient_diets(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List patient diets scoped to a patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/patient_diets", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # PATIENT ORDER ENDPOINTS
    # =============================================================================

    async def get_patient_orders(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patient orders

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patient_orders", params)
        return await self._process_response(response, flatten)

    async def get_patient_order(
        self,
        patient_order_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Fetch Details of a Patient Order

        Args:
            patient_order_id: Patient Order ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patient_orders/{patient_order_id}", params)
        return await self._process_response(response, flatten)

    async def get_patient_patient_orders(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patient orders scoped to a patient

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/patient_orders", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # UTILIZATION REVIEW ENDPOINTS
    # =============================================================================

    async def get_patient_ur(
        self,
        patient_id: str,
        params: Optional[Dict[str, Any]] = None,
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List a patient's utilization reviews

        Args:
            patient_id: Patient ID
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get(f"/api/patients/{patient_id}/ur", params)
        return await self._process_response(response, flatten)

    async def get_utilization_reviews_latest(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List utilization reviews with updated_at within a date range

        Args:
            params: Query parameters (start_date, end_date)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/utilization_reviews/latest", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # ADMINISTRATIVE ENDPOINTS
    # =============================================================================

    async def get_locations(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all locations

        Args:
            params: Query parameters (include_buildings)
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/locations", params)
        return await self._process_response(response, flatten)

    async def get_care_levels(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all Levels of Care

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/care_levels", params)
        return await self._process_response(response, flatten)

    async def get_flags(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all flags

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/flags", params)
        return await self._process_response(response, flatten)

    async def get_flag_categories(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all flag categories

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/flag_categories", params)
        return await self._process_response(response, flatten)

    async def get_patient_colors(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patient colors

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patient_colors", params)
        return await self._process_response(response, flatten)

    async def get_patient_tags(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patient tags

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patient_tags", params)
        return await self._process_response(response, flatten)

    async def get_patient_settings(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all patient settings

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/patient_settings", params)
        return await self._process_response(response, flatten)

    async def get_settings_payors(
        self, params: Optional[Dict[str, Any]] = None, flatten: Optional[bool] = None
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        List all payors

        Args:
            params: Query parameters
            flatten: Override auto_flatten setting
        """
        response = await self.get("/api/settings/payors", params)
        return await self._process_response(response, flatten)

    # =============================================================================
    # EXTERNAL ID MAPPING ENDPOINTS
    # =============================================================================

    async def update_patient_ext_id_mapping(
        self,
        patient_id: str,
        mapping_id: str,
        mapping_data: Dict[str, Any],
        flatten: Optional[bool] = None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Update an external id mapping

        Args:
            patient_id: Patient ID
            mapping_id: Mapping ID
            mapping_data: Updated mapping data
            flatten: Override auto_flatten setting
        """
        response = await self.patch(
            f"/api/patients/{patient_id}/ext_id_mappings/{mapping_id}", mapping_data
        )
        return await self._process_response(response, flatten)
