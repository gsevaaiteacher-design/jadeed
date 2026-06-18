from license_engine import license_engine

# Step 1: Activate (Key create aur encrypt karke dekho)
print("--- Testing Activation ---")
result = license_engine.activate("ZSTUDIO-PRO-2026-ROCK")
print(f"Status: {result['status']}")

# Step 2: Verify (Vahi vault read karke dekho)
if result['status'] == "SUCCESS":
    print("\n--- Testing Verification ---")
    val = license_engine.verify()
    print(f"Verification Status: {val['status']}")
    if 'lic' in val:
        print(f"License ID found: {val['lic']}")