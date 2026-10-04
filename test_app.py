from app import app

client = app.test_client()

routes_to_test = [
    ("/", 200),
    ("/dashboard", 200),
    ("/resume", 200),
    ("/interview-setup", 200),
    ("/result/1", 200),
    ("/prepare/1", 200),
    ("/progress", 200),
    ("/login", 200)
]

print("Running test suite on all Flask routes...")
all_passed = True
for route, expected_code in routes_to_test:
    res = client.get(route)
    if res.status_code == expected_code:
        print(f"  [PASS] {route} returned status {res.status_code}")
    else:
        print(f"  [FAIL] {route} returned status {res.status_code}, expected {expected_code}")
        all_passed = False

if all_passed:
    print("\nALL ROUTES AND TEMPLATES PASSED VERIFICATION!")
else:
    print("\nSome routes encountered errors.")
