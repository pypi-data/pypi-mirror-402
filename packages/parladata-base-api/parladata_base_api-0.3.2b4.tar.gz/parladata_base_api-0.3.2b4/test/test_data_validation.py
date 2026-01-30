"""
Simple test to verify test data structure without API calls

This script validates the generated test data structure locally
before sending it to the API.
"""

from data import generate_test_data


def test_data_structure():
    """Test that generated data has correct structure"""
    print("Generating test data...")
    data = generate_test_data()

    print("\n" + "=" * 70)
    print("RUNNING STRUCTURE VALIDATION TESTS")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Mandate exists
    print("\n[TEST 1] Mandate validation")
    try:
        assert data["mandate"] is not None
        assert "id" in data["mandate"]
        assert "beginning" in data["mandate"]
        print("  ✓ Mandate structure is valid")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ Mandate validation failed: {e}")
        tests_failed += 1

    # Test 2: Organizations count
    print("\n[TEST 2] Organizations count")
    try:
        assert len(data["organizations"]) == 7  # 1 root + 1 house + 3 PG + 2 committees
        print(f"  ✓ Expected 7 organizations, found {len(data['organizations'])}")
        tests_passed += 1
    except AssertionError:
        print(f"  ✗ Expected 7 organizations, found {len(data['organizations'])}")
        tests_failed += 1

    # Test 3: Organizations have required fields
    print("\n[TEST 3] Organization fields validation")
    try:
        for org in data["organizations"]:
            assert "id" in org
            assert "name" in org
            assert "parser_names" in org
            assert "classification" in org
        print("  ✓ All organizations have required fields")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ Organization field validation failed: {e}")
        tests_failed += 1

    # Test 4: Organization classifications
    print("\n[TEST 4] Organization classifications")
    try:
        classifications = [org["classification"] for org in data["organizations"]]
        assert "root" in classifications
        assert "house" in classifications
        assert classifications.count("pg") == 3
        assert classifications.count("committee") == 2
        print("  ✓ Organization classifications are correct")
        print(f"    - root: 1, house: 1, pg: 3, committee: 2")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ Classification validation failed: {e}")
        tests_failed += 1

    # Test 5: People count
    print("\n[TEST 5] People count")
    try:
        assert len(data["people"]) == 10  # 5 + 4 + 1
        print(f"  ✓ Expected 10 people, found {len(data['people'])}")
        tests_passed += 1
    except AssertionError:
        print(f"  ✗ Expected 10 people, found {len(data['people'])}")
        tests_failed += 1

    # Test 6: People have required fields
    print("\n[TEST 6] People fields validation")
    try:
        for person in data["people"]:
            assert "id" in person
            assert "name" in person
            assert "parser_names" in person
            assert "_pg_key" in person
            assert "_pg_role" in person
        print("  ✓ All people have required fields")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ People field validation failed: {e}")
        tests_failed += 1

    # Test 7: People roles distribution
    print("\n[TEST 7] People roles distribution")
    try:
        roles = [person["_pg_role"] for person in data["people"]]
        assert roles.count("president") == 3  # One per PG
        assert roles.count("deputy") == 2  # Only in PG1 and PG2
        assert roles.count("member") == 5  # Rest
        print("  ✓ Role distribution is correct")
        print(f"    - presidents: 3, deputies: 2, members: 5")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ Role distribution validation failed: {e}")
        tests_failed += 1

    # Test 8: Organization memberships count
    print("\n[TEST 8] Organization memberships count")
    try:
        # 1 (house in root) + 3 (PGs in house) = 4
        assert len(data["organization_memberships"]) == 4
        print(
            f"  ✓ Expected 4 org memberships, found {len(data['organization_memberships'])}"
        )
        tests_passed += 1
    except AssertionError:
        print(
            f"  ✗ Expected 4 org memberships, found {len(data['organization_memberships'])}"
        )
        tests_failed += 1

    # Test 9: Person memberships count
    print("\n[TEST 9] Person memberships count")
    try:
        # Each person has 2 memberships: party + voter
        assert len(data["person_memberships"]) == 20  # 10 people * 2
        print(
            f"  ✓ Expected 20 person memberships, found {len(data['person_memberships'])}"
        )
        tests_passed += 1
    except AssertionError:
        print(
            f"  ✗ Expected 20 person memberships, found {len(data['person_memberships'])}"
        )
        tests_failed += 1

    # Test 10: Person memberships structure
    print("\n[TEST 10] Person memberships structure")
    try:
        party_memberships = [
            m for m in data["person_memberships"] if m["role"] != "voter"
        ]
        voter_memberships = [
            m for m in data["person_memberships"] if m["role"] == "voter"
        ]

        assert len(party_memberships) == 10
        assert len(voter_memberships) == 10

        # All party memberships should have on_behalf_of=None
        assert all(m["on_behalf_of"] is None for m in party_memberships)

        # All voter memberships should have on_behalf_of set
        assert all(m["on_behalf_of"] is not None for m in voter_memberships)

        print("  ✓ Person memberships structure is correct")
        print(f"    - Party memberships: {len(party_memberships)}")
        print(f"    - Voter memberships: {len(voter_memberships)}")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ Person memberships structure validation failed: {e}")
        tests_failed += 1

    # Test 11: Each person has exactly 2 memberships
    print("\n[TEST 11] Each person has 2 memberships")
    try:
        person_ids = [p["id"] for p in data["people"]]
        for person_id in person_ids:
            memberships = [
                m for m in data["person_memberships"] if m["member"] == person_id
            ]
            assert (
                len(memberships) == 2
            ), f"Person {person_id} has {len(memberships)} memberships"

            # One party, one voter
            roles = [m["role"] for m in memberships]
            assert "voter" in roles
            assert any(r in ["president", "deputy", "member"] for r in roles)

        print("  ✓ Each person has exactly 2 memberships (1 party + 1 voter)")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ Membership count per person validation failed: {e}")
        tests_failed += 1

    # Test 12: Single member PG has president role
    print("\n[TEST 12] Single member PG has president role")
    try:
        # Find PG3 (Green Movement - single member)
        pg3_members = [p for p in data["people"] if p["_pg_key"] == "pg3"]
        assert len(pg3_members) == 1
        assert pg3_members[0]["_pg_role"] == "president"
        print("  ✓ Single member PG correctly has president role")
        tests_passed += 1
    except AssertionError as e:
        print(f"  ✗ Single member PG validation failed: {e}")
        tests_failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {tests_passed}/12")
    print(f"Tests failed: {tests_failed}/12")

    if tests_failed == 0:
        print("\n✓ All tests passed! Data structure is valid.")
        return True
    else:
        print(f"\n✗ {tests_failed} test(s) failed. Please review the data structure.")
        return False


def print_detailed_breakdown():
    """Print detailed breakdown of test data"""
    data = generate_test_data()

    print("\n" + "=" * 70)
    print("DETAILED DATA BREAKDOWN")
    print("=" * 70)

    # Organizations by type
    print("\nOrganizations by type:")
    for classification in ["root", "house", "pg", "committee"]:
        orgs = [
            o for o in data["organizations"] if o["classification"] == classification
        ]
        print(f"  {classification}: {len(orgs)}")
        for org in orgs:
            print(f"    - {org['name']} (ID: {org['id']})")

    # People by PG
    print("\nPeople by Parliamentary Group:")
    for pg_key in ["pg1", "pg2", "pg3"]:
        people = [p for p in data["people"] if p["_pg_key"] == pg_key]
        pg_name = next(
            o["name"]
            for o in data["organizations"]
            if o.get("id") == int(pg_key.replace("pg", "")) + 2
        )
        print(f"  {pg_name}: {len(people)}")
        for person in people:
            print(f"    - {person['name']} ({person['_pg_role']})")

    # Memberships breakdown
    print("\nMemberships breakdown:")
    print(f"  Organization memberships: {len(data['organization_memberships'])}")
    for om in data["organization_memberships"]:
        member_org = next(o for o in data["organizations"] if o["id"] == om["member"])
        parent_org = next(
            o for o in data["organizations"] if o["id"] == om["organization"]
        )
        print(f"    - {member_org['name']} → {parent_org['name']}")

    print(f"\n  Person memberships: {len(data['person_memberships'])}")
    print(
        f"    - Party memberships: {len([m for m in data['person_memberships'] if m['role'] != 'voter'])}"
    )
    print(
        f"    - Voter memberships: {len([m for m in data['person_memberships'] if m['role'] == 'voter'])}"
    )


if __name__ == "__main__":
    # Run validation tests
    success = test_data_structure()

    # Print detailed breakdown
    print_detailed_breakdown()

    # Exit with appropriate code
    exit(0 if success else 1)
