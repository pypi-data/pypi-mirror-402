"""
Integration test for Parladata Base API

This script tests the complete workflow of:
1. Creating test data (mandate, organizations, people)
2. Sending data to Parladata API
3. Loading data through storage classes
4. Processing memberships
5. Verifying data integrity
"""

import logging
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict

from data import generate_test_data

from parladata_base_api.storages.storage import DataStorage

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ParladataAPITester:
    """Test the complete Parladata Base API workflow"""

    def __init__(
        self,
        api_url: str,
        api_username: str,
        api_password: str,
    ):
        self.api_url = api_url
        self.api_username = api_username
        self.api_password = api_password
        self.test_data = None
        self.storage = None
        self.created_ids = {
            "mandate": None,
            "organizations": {},
            "people": {},
            "organization_memberships": {},
            "person_memberships": {},
        }

    def run_full_test(self) -> bool:
        """Run complete test suite"""
        try:
            logger.info("=" * 70)
            logger.info("STARTING PARLADATA API INTEGRATION TEST")
            logger.info("=" * 70)

            # Step 1: Generate test data
            logger.info("\n[1/6] Generating test data...")
            self.test_data = generate_test_data()

            # Step 2: Create mandate
            logger.info("\n[2/6] Creating mandate via API...")
            self._create_mandate()

            # Step 3: Initialize temporary storage for creating data
            logger.info("\n[3/6] Initializing temporary storage...")
            self._initialize_temp_storage()

            # Step 4: Create organizations
            logger.info("\n[4/6] Creating organizations via storage...")
            self._create_organizations()

            # Step 5: Create people
            logger.info("\n[5/6] Creating people via storage...")
            self._create_people()

            # Step 6: Re-initialize storage with correct main_org_id
            logger.info(
                "\n[6/6] Re-initializing DataStorage with final configuration..."
            )
            self._initialize_storage()

            # Step 7: Create memberships
            logger.info("\n[7/7] Creating memberships via storage...")
            self._create_organization_memberships()
            self._create_person_memberships()

            # Verification
            # Verification
            logger.info("\n[VERIFICATION] Verifying data integrity...")
            self._verify_data()

            logger.info("\n" + "=" * 70)
            logger.info("TEST COMPLETED SUCCESSFULLY!")
            logger.info("=" * 70)
            return True

        except Exception as e:
            logger.error(f"\n[ERROR] Test failed: {e}", exc_info=True)
            return False

    def _initialize_temp_storage(self) -> None:
        """Initialize temporary storage for creating organizations and people"""
        self.temp_storage = DataStorage(
            mandate_id=self.created_ids["mandate"],
            mandate_start_time=datetime.strptime(
                self.test_data["mandate"]["beginning"], "%Y-%m-%d"
            ),
            main_org_id=1,  # Temporary, will be set properly later
            api_url=self.api_url,
            api_auth_username=self.api_username,
            api_auth_password=self.api_password,
        )
        logger.info(self.temp_storage.mandate_start_time)
        logger.info(f"  Initialized temporary storage for data creation")

    def _create_mandate(self) -> None:
        """Create mandate through API"""
        mandate_data = self.test_data["mandate"]

        from parladata_base_api.api.endpoints import ParladataApi

        api = ParladataApi(self.api_url, self.api_username, self.api_password)

        # Check if mandate already exists
        existing_mandates = api.mandates.get_all()
        for mandate in existing_mandates:
            if mandate["description"] == mandate_data["description"]:
                self.created_ids["mandate"] = mandate["id"]
                logger.info(
                    f"  Mandate already exists: {mandate['description']} (ID: {mandate['id']})"
                )
                return

        # Create new mandate
        result = api.mandates.set(mandate_data)
        self.created_ids["mandate"] = result["id"]
        logger.info(f"  Created mandate: {result['description']} (ID: {result['id']})")

    def _create_organizations(self) -> None:
        """Create organizations through storage"""
        for org in self.test_data["organizations"]:
            # Use storage to get or add organization
            # get_or_add_object will check if organization exists by parser_names
            org_obj = self.temp_storage.organization_storage.get_or_add_object(org)

            self.created_ids["organizations"][org["id"]] = org_obj.id

            if org_obj.is_new:
                logger.info(
                    f"  Created organization: {org_obj.name} (ID: {org_obj.id})"
                )
            else:
                logger.info(
                    f"  Organization already exists: {org_obj.name} (ID: {org_obj.id})"
                )

    def _create_people(self) -> None:
        """Create people through storage"""
        for person in self.test_data["people"]:
            # Use storage to get or add person
            # get_or_add_object will check if person exists by parser_names
            person_obj = self.temp_storage.people_storage.get_or_add_object(person)

            self.created_ids["people"][person["id"]] = person_obj.id

            if person_obj.is_new:
                logger.info(
                    f"  Created person: {person_obj.name} (ID: {person_obj.id})"
                )
            else:
                logger.info(
                    f"  Person already exists: {person_obj.name} (ID: {person_obj.id})"
                )

    def _initialize_storage(self) -> None:
        """Initialize DataStorage with test mandate"""
        mandate_id = self.created_ids["mandate"]

        # Get actual house (main org) ID
        root_org_id = self.created_ids["organizations"][1]  # Root org
        house_org_id = self.created_ids["organizations"][2]  # House org

        self.storage = DataStorage(
            mandate_id=mandate_id,
            mandate_start_time=datetime.strptime(
                self.test_data["mandate"]["beginning"], "%Y-%m-%d"
            ),
            main_org_id=house_org_id,
            api_url=self.api_url,
            api_auth_username=self.api_username,
            api_auth_password=self.api_password,
        )

        logger.info(f"  Initialized DataStorage for mandate {mandate_id}")
        logger.info(f"  Main organization ID: {house_org_id}")

    def _create_organization_memberships(self) -> None:
        """Create organization memberships through storage"""
        for org_membership in self.test_data["organization_memberships"]:
            # Map test IDs to real IDs
            real_member_id = self.created_ids["organizations"][org_membership["member"]]
            real_org_id = self.created_ids["organizations"][
                org_membership["organization"]
            ]
            real_mandate_id = self.created_ids["mandate"]

            membership_data = {
                "member": real_member_id,
                "organization": real_org_id,
                "start_time": org_membership["start_time"],
                "end_time": org_membership["end_time"],
                "mandate": real_mandate_id,
            }
            logger.info(f"  Processing org membership data: {membership_data}")

            # Use storage to get or add organization membership
            org_membership_obj = (
                self.storage.organization_membership_storage.get_or_add_object(
                    membership_data
                )
            )

            self.created_ids["organization_memberships"][
                org_membership["id"]
            ] = org_membership_obj.id

            if org_membership_obj.is_new:
                logger.info(
                    f"  Created org membership: Org {real_member_id} -> Org {real_org_id} (ID: {org_membership_obj.id})"
                )
            else:
                logger.info(
                    f"  Org membership already exists: Org {real_member_id} -> Org {real_org_id} (ID: {org_membership_obj.id})"
                )

    def _create_person_memberships(self) -> None:
        """Create person memberships through storage"""
        per_person_data = defaultdict(lambda: defaultdict(list))
        assembly = self.storage.organization_storage.get_or_add_object(
            {
                "name": self.test_data["house"]["name"],
            }
        )
        for person_membership in self.test_data["person_memberships"]:
            person = self.storage.people_storage.get_or_add_object(
                {"name": person_membership["member"]}
            )
            organization = self.storage.organization_storage.get_or_add_object(
                {
                    "name": person_membership["organization"],
                    "parser_names": person_membership["organization"],
                    "classification": "pg",
                }
            )
            role = person_membership["role"]
            typ = person_membership.get("type", "party")

            # self.storage.membership_storage.get_or_add_object(
            #     {
            #         "member": person.id,
            #         "organization": organization.id,
            #         "on_behalf_of": None,
            #         "role": role,
            #         "start_time": person_membership["start_time"],
            #         "end_time": person_membership["end_time"],
            #         "mandate": self.storage.mandate_id,
            #     }
            # )
            # self.storage.membership_storage.get_or_add_object(
            #     {
            #         "member": person.id,
            #         "on_behalf_of": organization.id,
            #         "organization": assembly.id,
            #         "role": "voter",
            #         "start_time": person_membership["start_time"],
            #         "end_time": person_membership["end_time"],
            #         "mandate": self.storage.mandate_id,
            #     }
            # )

            per_person_data[person.id][typ].append(
                {
                    "is_voter": True,
                    "member": person,
                    # "organization": assembly,
                    # "on_behalf_of": organization,
                    "organization": organization,
                    "on_behalf_of": None,
                    "role": role,
                    "type": typ,
                    "start_time": person_membership["start_time"],
                    "end_time": person_membership["end_time"],
                    "mandate": self.storage.mandate_id,
                }
            )

        # fix person organizations and on_behalf_of
        for person_memberships in per_person_data.values():
            party = person_memberships.get("party", None)
            if party:
                party = party[0]
                party["on_behalf_of"] = party["organization"]
                party["organization"] = assembly

            for membership in person_memberships.get("commitee", []):
                membership["on_behalf_of"] = party["on_behalf_of"]

        # Update memberships in parladata
        self.storage.membership_storage.temporary_data = per_person_data
        self.storage.membership_storage.refresh_per_person_memberships()

    def _verify_data(self) -> None:
        """Verify that data was created correctly"""
        logger.info("\n  Verification Results:")
        logger.info(
            f"    - Organizations created: {len(self.created_ids['organizations'])}"
        )
        logger.info(f"    - People created: {len(self.created_ids['people'])}")
        logger.info(
            f"    - Org memberships created: {len(self.created_ids['organization_memberships'])}"
        )
        logger.info(
            f"    - Person memberships created: {len(self.created_ids['person_memberships'])}"
        )

        # Load and verify through storage
        self.storage.membership_storage.load_data()
        logger.info(
            f"    - Memberships loaded in storage: {len(self.storage.membership_storage.memberships)}"
        )

        # Verify active voters
        active_voters_count = sum(
            len(on_behalf_orgs)
            for orgs in self.storage.membership_storage.active_voters.values()
            for on_behalf_orgs in orgs.values()
        )
        logger.info(f"    - Active voters tracked: {active_voters_count}")


def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Parladata Base API")
    parser.add_argument("--api-url", required=True, help="Parladata API URL")
    parser.add_argument("--username", required=True, help="API username")
    parser.add_argument("--password", required=True, help="API password")

    args = parser.parse_args()

    tester = ParladataAPITester(
        api_url=args.api_url,
        api_username=args.username,
        api_password=args.password,
    )

    success = tester.run_full_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
    main()
