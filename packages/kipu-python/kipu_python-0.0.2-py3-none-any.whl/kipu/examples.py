"""
Example usage of the Kipu API library
Demonstrates various API operations and response handling
"""

import asyncio

from .client import KipuClient


class KipuExamples:
    def __init__(self, access_id: str, secret_key: str, app_id: str):
        self.access_id = access_id
        self.secret_key = secret_key
        self.app_id = app_id

    async def basic_patient_operations(self):
        """
        Example: Basic patient operations
        """
        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            # Get patient census (returns flattened DataFrame by default)
            print("Getting patient census...")
            census_df = await client.get_patients_census(
                params={"phi_level": "high", "page": 1, "per": 10}
            )
            print(f"Census DataFrame shape: {census_df.shape}")
            print("Census columns:", list(census_df.columns))

            # Get specific patient (raw JSON response)
            if not census_df.empty:
                patient_id = (
                    census_df.iloc[0]["id"]
                    if "id" in census_df.columns
                    else "sample_id"
                )
                print(f"\nGetting patient {patient_id}...")
                patient_data = await client.get_patient(
                    patient_id,
                    params={"include_ids": True},
                    flatten=False,  # Get raw JSON
                )
                print("Patient data keys:", list(patient_data.keys()))

    async def medical_records_operations(self):
        """
        Example: Medical records operations
        """
        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            # Get vital signs for all patients
            print("Getting all vital signs...")
            vital_signs_df = await client.get_vital_signs()
            print(f"Vital signs DataFrame shape: {vital_signs_df.shape}")

            # Get patient-specific vital signs
            patient_id = "sample_patient_id"
            print(f"\nGetting vital signs for patient {patient_id}...")
            patient_vitals_df = await client.get_patient_vital_signs(
                patient_id,
                params={
                    "created_at_start_date": "2024-01-01",
                    "created_at_end_date": "2024-12-31",
                },
            )
            print(f"Patient vital signs shape: {patient_vitals_df.shape}")

            # Get allergies
            print("\nGetting all allergies...")
            allergies_df = await client.get_allergies()
            print(f"Allergies DataFrame shape: {allergies_df.shape}")

    async def appointment_operations(self):
        """
        Example: Appointment operations
        """
        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            # Get all appointments with date range
            print("Getting appointments...")
            appointments_df = await client.get_scheduler_appointments(
                params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
            )
            print(f"Appointments DataFrame shape: {appointments_df.shape}")

            # Get appointment types
            print("\nGetting appointment types...")
            types_df = await client.get_scheduler_appointment_types()
            print(f"Appointment types shape: {types_df.shape}")

            # Get appointment statuses
            print("\nGetting appointment statuses...")
            statuses_df = await client.get_scheduler_appointment_statuses()
            print(f"Appointment statuses shape: {statuses_df.shape}")

    async def administrative_operations(self):
        """
        Example: Administrative operations
        """
        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            # Get locations
            print("Getting locations...")
            locations_df = await client.get_locations(
                params={"include_buildings": True}
            )
            print(f"Locations DataFrame shape: {locations_df.shape}")

            # Get users
            print("\nGetting users...")
            users_df = await client.get_users()
            print(f"Users DataFrame shape: {users_df.shape}")

            # Get providers
            print("\nGetting providers...")
            providers_df = await client.get_providers()
            print(f"Providers DataFrame shape: {providers_df.shape}")

            # Get roles
            print("\nGetting roles...")
            roles_df = await client.get_roles()
            print(f"Roles DataFrame shape: {roles_df.shape}")

    async def create_patient_example(self):
        """
        Example: Creating a new patient
        """
        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            # Patient data structure
            patient_data = {
                "document": {
                    "recipient_id": self.app_id,
                    "data": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "dob": "1990-01-01",
                        "gender": "M",
                        "address_street": "123 Main St",
                        "address_city": "New York",
                        "state": "NY",
                        "address_zip": "10001",
                        "phone": "(555) 123-4567",
                        "email": "john.doe@example.com",
                    },
                }
            }

            # Create patient
            print("Creating new patient...")
            created_patient = await client.create_patient(patient_data, flatten=False)
            print("Created patient ID:", created_patient.get("id"))
            return created_patient.get("id")

    async def create_vital_signs_example(self, patient_id: str):
        """
        Example: Creating vital signs for a patient
        """
        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            # Vital signs data
            vital_signs_data = {
                "document": {
                    "recipient_id": self.app_id,
                    "data": {
                        "systolic_blood_pressure": 120,
                        "diastolic_blood_pressure": 80,
                        "heart_rate": 72,
                        "temperature": 98.6,
                        "respiratory_rate": 16,
                        "oxygen_saturation": 99,
                        "weight": 150.5,
                        "height": 70,
                        "comments": "Normal vital signs",
                    },
                }
            }

            # Create vital signs
            print(f"Creating vital signs for patient {patient_id}...")
            created_vitals = await client.create_patient_vital_signs(
                patient_id, vital_signs_data, flatten=False
            )
            print("Created vital signs ID:", created_vitals.get("id"))

    async def error_handling_example(self):
        """
        Example: Error handling
        """
        from .exceptions import KipuAPIError, KipuNotFoundError

        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            try:
                # Try to get a non-existent patient
                await client.get_patient("non_existent_id")
            except KipuNotFoundError as e:
                print(f"Patient not found: {e.message}")
                print(f"Status code: {e.status_code}")
            except KipuAPIError as e:
                print(f"API error: {e.message}")
                print(f"Status code: {e.status_code}")
                print(f"Response data: {e.response_data}")

    async def flattening_comparison_example(self):
        """
        Example: Comparing flattened vs raw responses
        """
        async with KipuClient(self.access_id, self.secret_key, self.app_id) as client:

            # Get raw JSON response
            print("Getting raw patient data...")
            raw_data = await client.get_patients_census(
                params={"per": 2}, flatten=False
            )
            print("Raw data type:", type(raw_data))
            print(
                "Raw data structure:",
                (
                    list(raw_data.keys())
                    if isinstance(raw_data, dict)
                    else "List of records"
                ),
            )

            # Get flattened DataFrame
            print("\nGetting flattened patient data...")
            flattened_df = await client.get_patients_census(
                params={"per": 2}, flatten=True
            )
            print("Flattened data type:", type(flattened_df))
            print("DataFrame shape:", flattened_df.shape)
            print("DataFrame columns:", list(flattened_df.columns))

    async def run_all_examples(self):
        """
        Run all examples
        """
        print("=" * 60)
        print("KIPU API library EXAMPLES")
        print("=" * 60)

        try:
            # Basic operations
            await self.basic_patient_operations()
            print("\n" + "-" * 60)

            # Medical records
            await self.medical_records_operations()
            print("\n" + "-" * 60)

            # Appointments
            await self.appointment_operations()
            print("\n" + "-" * 60)

            # Administrative
            await self.administrative_operations()
            print("\n" + "-" * 60)

            # Error handling
            await self.error_handling_example()
            print("\n" + "-" * 60)

            # Flattening comparison
            await self.flattening_comparison_example()
            print("\n" + "-" * 60)

            # # Create operations (commented out for safety)
            # patient_id = await self.create_patient_example()
            # if patient_id:
            #     await self.create_vital_signs_example(patient_id)

        except Exception as e:
            print(f"Example execution error: {e}")

        print("\nExamples completed!")


# Usage example
async def main():
    # Initialize with your credentials
    examples = KipuExamples(
        access_id="your_access_id",
        secret_key="your_secret_key",
        app_id="your_app_id",  # nosec
    )

    # Run all examples
    await examples.run_all_examples()


if __name__ == "__main__":
    asyncio.run(main())
