import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get("SERVICE_URL", "http://localhost:5000")

BUG_SCENARIOS = {
    "value_error": {
        "name": "ValueError in /api/calculate (a='abc')",
        "method": "POST",
        "url": f"{BASE_URL}/api/calculate",
        "json": {"a": "abc", "b": 2},
        "expected_status": 500,
        "expected_error": "ValueError",
    },
    "zero_division": {
        "name": "ZeroDivisionError in /api/calculate (b=0)",
        "method": "POST",
        "url": f"{BASE_URL}/api/calculate",
        "json": {"a": 10, "b": 0},
        "expected_status": 500,
        "expected_error": "ZeroDivisionError",
    },
    "attribute_error": {
        "name": "AttributeError in /api/greet (name=None)",
        "method": "GET",
        "url": f"{BASE_URL}/api/greet",
        "json": {},
        "expected_status": 500,
        "expected_error": "AttributeError",
    },
}


def trigger_bug(bug_key: str) -> dict:
    scenario = BUG_SCENARIOS.get(bug_key)
    if not scenario:
        print(f"Unknown bug key: {bug_key}")
        print(f"Available bug keys: {', '.join(BUG_SCENARIOS.keys())}")
        return {"success": False, "error": "Unknown bug key"}

    print(f"Trigger bug scenario: {scenario['name']}")
    try:
        if scenario["method"] == "GET":
            response = requests.get(scenario["url"], json=scenario["json"], timeout=5)
        else:
            response = requests.post(scenario["url"], json=scenario["json"], timeout=5)

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        print(f"Expected status: {scenario['expected_status']} ({scenario['expected_error']})")
        if response.status_code != scenario["expected_status"]:
            print("Warning: status does not match expectation. Restart service to load latest app.py.")
        return {"success": True, "status_code": response.status_code}
    except requests.exceptions.ConnectionError:
        print("Error: could not connect to service. Is demo_service running?")
        return {"success": False, "error": "Connection refused"}
    except Exception as error:
        print(f"Error: {error}")
        return {"success": False, "error": str(error)}


def trigger_all_bugs():
    print("Trigger all bug scenarios...\n")
    for key in BUG_SCENARIOS:
        trigger_bug(key)
        print()
    print("Done. Check demo_service/logs/error.log for tracebacks.")


def main():
    if len(sys.argv) > 1:
        bug_key = sys.argv[1]
        if bug_key == "all":
            trigger_all_bugs()
        else:
            trigger_bug(bug_key)
        return

    print("Bug trigger script")
    print("=" * 40)
    print("Available bug keys:")
    for key, scenario in BUG_SCENARIOS.items():
        print(f"  {key}: {scenario['name']}")
    print()
    print("Usage:")
    print(f"  python {sys.argv[0]} <bug_key>")
    print(f"  python {sys.argv[0]} all")
    print()
    print("Tip:")
    print("  Run reset_bug.ps1 before triggering, to switch app.py to matching bug base.")
    print("  Example: powershell -ExecutionPolicy Bypass -File scripts/reset_bug.ps1 -Bug value_error")


if __name__ == "__main__":
    main()
