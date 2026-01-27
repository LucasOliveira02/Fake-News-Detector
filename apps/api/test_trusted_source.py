import requests
import json

def test_api():
    url = "http://localhost:8000/predict"
    
    print("--- Test Case 1: Trusted Source (URL Present) ---")
    payload_trusted = {"text": "Check this article from https://www.bbc.com/news regarding the event."}
    try:
        response = requests.post(url, json=payload_trusted)
        data = response.json()
        print(json.dumps(data, indent=2))
        if "details" in data:
            print(f"Details: {data['details']}")
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 2: Untrusted Source ---")
    payload_untrusted = {"text": "Check this random blog http://random-blog.com"}
    try:
        response = requests.post(url, json=payload_untrusted)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 3: Source Named but No URL (Suspicious) ---")
    payload_suspicious = {"text": "According to BBC News, the sky is green today."}
    try:
        response = requests.post(url, json=payload_suspicious)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Test Case 4: Source Named AND URL Present (Valid) ---")
    payload_valid = {"text": "According to BBC News, the sky is blue. Source: https://www.bbc.com/news"}
    try:
        response = requests.post(url, json=payload_valid)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_api()
