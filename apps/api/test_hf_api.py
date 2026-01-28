import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

api_key = os.environ.get("HUGGINGFACE_API_KEY")
print(f"Testing with Key: {api_key[:4]}..." if api_key else "No Key Found")

# Initialize client
client = InferenceClient(token=api_key)
model_id = "sentence-transformers/all-MiniLM-L6-v2"

print(f"Sending request to {model_id} via InferenceClient...")

try:
    response = client.feature_extraction(
        "This is a test sentence.",
        model=model_id
    )
    print("Success!")
    print(f"Response: {response}")

except Exception as e:
    print(f"Error: {e}")
