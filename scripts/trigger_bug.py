import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get("SERVICE_URL", "http://localhost:5000")

BUG_SCENARIOS = {
    "1": {
        "name": "KeyError - missing user_id",
        "method": "GET",
        "url": f"{BASE_URL}/api/user",
        "json": {},
        "expected_error": "KeyError",
    },
    "2": {
        "name": "TypeError - string/int concatenation",
        "method": "POST",
        "url": f"{BASE_URL}/api/calculate",
        "json": {"a": 10, "b": 2},
        "expected_error": "TypeError",
    },
    "3": {
        "name": "ZeroDivisionError - division by zero",
        "method": "POST",
        "url": f"{BASE_URL}/api/calculate",
        "json": {"a": 10, "b": 0},
        "expected_error": "ZeroDivisionError",
    },
    "4": {
        "name": "TypeError - NoneType subtraction",
        "method": "POST",
        "url": f"{BASE_URL}/api/discount",
        "json": {"discount": 20},
        "expected_error": "TypeError",
    },
    "5": {
        "name": "AttributeError - NoneType has no upper",
        "method": "GET",
        "url": f"{BASE_URL}/api/greet",
        "json": {},
        "expected_error": "AttributeError",
    },
}


def trigger_bug(scenario_key: str) -> dict:
    scenario = BUG_SCENARIOS.get(scenario_key)
    if not scenario:
        print(f"Unknown scenario: {scenario_key}")
        print(f"Available scenarios: {', '.join(BUG_SCENARIOS.keys())}")
        return {"success": False, "error": "Unknown scenario"}

    print(f"Triggering bug scenario {scenario_key}: {scenario['name']}")
    try:
        if scenario["method"] == "GET":
            resp = requests.get(scenario["url"], json=scenario["json"], timeout=5)
        else:
            resp = requests.post(scenario["url"], json=scenario["json"], timeout=5)
        print(f"Response status: {resp.status_code}")
        print(f"Response body: {resp.text[:500]}")
        return {"success": True, "status_code": resp.status_code}
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to service. Is it running?")
        return {"success": False, "error": "Connection refused"}
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}


def trigger_all_bugs():
    print("Triggering all bug scenarios...\n")
    for key in BUG_SCENARIOS:
        trigger_bug(key)
        print()
    print("All bug scenarios triggered. Check the log file for tracebacks.")


def main():
    if len(sys.argv) > 1:
        scenario_key = sys.argv[1]
        if scenario_key == "all":
            trigger_all_bugs()
        else:
            trigger_bug(scenario_key)
    else:
        print("Bug Trigger Script")
        print("=" * 40)
        print("Available scenarios:")
        for key, scenario in BUG_SCENARIOS.items():
            print(f"  {key}: {scenario['name']}")
        print()
        print("Usage:")
        print(f"  python {sys.argv[0]} <scenario_number>")
        print(f"  python {sys.argv[0]} all")


if __name__ == "__main__":
    main()
