#!/usr/bin/env python3
"""
Quick start example for Parladata Base API testing

This script demonstrates how to quickly generate and use test data.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.data import generate_test_data


def main():
    """Generate and display test data"""
    print("Generating Parladata test data...")
    print("=" * 70)

    # Generate data
    data = generate_test_data()

    print("\n" + "=" * 70)
    print("QUICK ACCESS EXAMPLES")
    print("=" * 70)

    # Example 1: Access mandate
    print("\n1. Accessing mandate:")
    print(f"   Mandate ID: {data['mandate']['id']}")
    print(f"   Name: {data['mandate']['name']}")
    print(f"   Period: {data['mandate']['beginning']} to {data['mandate']['end']}")

    # Example 2: Find organization by classification
    print("\n2. Finding organizations by classification:")
    house = next(
        org for org in data["organizations"] if org["classification"] == "house"
    )
    print(f"   House organization: {house['name']} (ID: {house['id']})")

    pgs = [org for org in data["organizations"] if org["classification"] == "pg"]
    print(f"   Parliamentary groups ({len(pgs)}):")
    for pg in pgs:
        print(f"     - {pg['name']} (ID: {pg['id']})")

    # Example 3: Find people by party
    print("\n3. Finding people by parliamentary group:")
    pg1_id = next(
        org["id"]
        for org in data["organizations"]
        if org["name"] == "Progressive Party Group"
    )

    # Find party memberships for PG1
    pg1_party_memberships = [
        m
        for m in data["person_memberships"]
        if m["organization"] == pg1_id and m["role"] != "voter"
    ]

    print(f"   Progressive Party Group members:")
    for membership in pg1_party_memberships:
        person = next(p for p in data["people"] if p["id"] == membership["member"])
        print(f"     - {person['name']} ({membership['role']})")

    # Example 4: Find voter memberships
    print("\n4. Checking voter memberships:")
    voter_memberships = [m for m in data["person_memberships"] if m["role"] == "voter"]
    print(f"   Total voter memberships: {len(voter_memberships)}")

    # Show first voter membership details
    first_voter = voter_memberships[0]
    person = next(p for p in data["people"] if p["id"] == first_voter["member"])
    org = next(
        o for o in data["organizations"] if o["id"] == first_voter["organization"]
    )
    on_behalf = next(
        o for o in data["organizations"] if o["id"] == first_voter["on_behalf_of"]
    )

    print(f"   Example: {person['name']}")
    print(f"     - Can vote in: {org['name']}")
    print(f"     - On behalf of: {on_behalf['name']}")

    # Example 5: Organization hierarchy
    print("\n5. Organization hierarchy:")
    org_memberships = data["organization_memberships"]
    for om in org_memberships:
        member_org = next(o for o in data["organizations"] if o["id"] == om["member"])
        parent_org = next(
            o for o in data["organizations"] if o["id"] == om["organization"]
        )
        print(f"   {member_org['name']} → {parent_org['name']}")

    # Example 6: Using the data with API
    print("\n" + "=" * 70)
    print("USAGE WITH API")
    print("=" * 70)
    print(
        """
To send this data to Parladata API:

    from test.test_api_integration import ParladataAPITester
    
    tester = ParladataAPITester(
        api_url="http://localhost:8000/v1",
        api_username="your_username",
        api_password="your_password"
    )
    
    tester.run_full_test()

Or use the command line:

    python test_api_integration.py \\
        --api-url "http://localhost:8000/v1" \\
        --username "your_username" \\
        --password "your_password"
    """
    )

    print("\n" + "=" * 70)
    print("For more information, see test/README.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
