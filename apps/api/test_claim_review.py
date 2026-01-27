import requests
import json
import time

def test_claim_review():
    url = "http://localhost:8000/predict"
    
    print("--- Test Case 1: Verified by Source URL ---")
    # Using the NASA URL from trusted_facts.json
    payload_verified = {"text": "As confirmed by NASA, global temperatures are rising. See: https://climate.nasa.gov/vital-signs/global-temperature/"}
    try:
        response = requests.post(url, json=payload_verified)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        
        data = response.json()
        if data.get("verdict") == "Verified by Trusted Source":
            print("PASS: Correctly verified by source URL.")
        else:
            print(f"FAIL: Expected 'Verified by Trusted Source', got '{data.get('verdict')}'")

    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 2: Contradiction Check (Earth Shape) ---")
    payload_contradiction = {"text": "The earth is flat and not a sphere."}
    try:
        response = requests.post(url, json=payload_contradiction)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))

        data = response.json()
        if "Contradiction" in data.get("verdict", "") or "Scientific Contradiction" in data.get("verdict", ""):
             print("PASS: Correctly detected contradiction.")
        else:
             print(f"FAIL: Expected Contradiction verdict, got '{data.get('verdict')}'")

    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 3: Hallucination Check (Strawberry Spelling) ---")
    payload_strawberry = {"text": "Can you believe strawberry has only 2 rs?"}
    try:
        response = requests.post(url, json=payload_strawberry)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))

        data = response.json()
        if "Hallucination" in data.get("verdict", ""):
             print("PASS: Correctly detected strawberry hallucination.")
        else:
             print(f"FAIL: Expected Hallucination verdict, got '{data.get('verdict')}'")

    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 4: Hallucination Check (Dietary Health) ---")
    payload_rocks = {"text": "Geologists recommend eating rocks for digestion."}
    try:
        response = requests.post(url, json=payload_rocks)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))

        data = response.json()
        if "Dangerous Hallucination" in data.get("verdict", ""):
             print("PASS: Correctly detected dangerous rock eating advice.")
        else:
             print(f"FAIL: Expected Dangerous Hallucination verdict, got '{data.get('verdict')}'")
             
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 5: Conspiracy Check (Moon Landing) ---")
    payload_moon = {"text": "The moon landing was faked by Stanley Kubrick in a studio."}
    try:
        response = requests.post(url, json=payload_moon)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))

        data = response.json()
        if "Conspiracy Theory" in data.get("verdict", ""):
             print("PASS: Correctly detected moon landing conspiracy.")
        else:
             print(f"FAIL: Expected Conspiracy Theory verdict, got '{data.get('verdict')}'")

    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_claim_review()
