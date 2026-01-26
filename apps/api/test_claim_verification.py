import requests
import json

def test_api():
    url = "http://localhost:8000/predict"
    
    print("--- Test Case 1: Fact Contradiction (Climate Cooling) ---")
    payload_contradiction = {"text": "Recent studies show that the climate is cooling rapidly and we are entering an ice age."}
    try:
        response = requests.post(url, json=payload_contradiction)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 2: Fact Embellishment (Temperature Rise > 5deg) ---")
    payload_embellish = {"text": "Global warming has caused temperatures to rise by 20 degrees instantly."}
    try:
        response = requests.post(url, json=payload_embellish)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 3: Scientific Contradiction (Flat Earth) ---")
    payload_flat = {"text": "The truth is that the earth is flat and not a sphere."}
    try:
        response = requests.post(url, json=payload_flat)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 4: Consistent Claim (Warming) ---")
    payload_ok = {"text": "Global warming is causing temperatures to rise around the globe."}
    try:
        response = requests.post(url, json=payload_ok)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_api()
