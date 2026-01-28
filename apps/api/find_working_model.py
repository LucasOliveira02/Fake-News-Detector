import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
api_key = os.environ.get("HUGGINGFACE_API_KEY")
client = InferenceClient(token=api_key)

candidates = [
    "distilbert-base-uncased-finetuned-sst-2-english", # The "Hello World" of HF
    "facebook/bart-large-mnli", # Zero-shot classifier (very reliable)
    "roberta-large-mnli", 
    "fake-news-detection/roberta-base-fake-news-detector", # Trying a specialized one again
    "openai-community/gpt2", # Generation model (just to check connectivity)
]

text = "This is a test."

print(f"Testing with Key Prefix: {api_key[:4] if api_key else 'None'}")

for model in candidates:
    print(f"\n--- Testing {model} ---")
    try:
        # Try simplest task first
        if "mnli" in model:
             res = client.zero_shot_classification(text, labels=["fake", "real"], model=model)
        else:
             res = client.text_classification(text, model=model)
             
        print(f"SUCCESS! Result: {res}")
        print(f"WINNER: {model}")
        break
    except Exception as e:
        print(f"FAILED: {e}")
