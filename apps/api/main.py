from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random
import time

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Allow our frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Fake News Detector API is running"}

@app.post("/predict")
async def predict_ai_usage(request: TextRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Simulate processing time
    time.sleep(1.5)

    # Placeholder AI Logic (Mock)
    # real logic would load a pytorch/tensorflow model here
    
    # Simple heuristic for demo: longer words might mean "smarter" (just for fun)
    # or just random for now as requested.
    
    # Let's make it slightly deterministic based on length so it's not totally random
    # but still feels "alive"
    
    word_count = len(request.text.split())
    
    # Load trusted sources
    import json
    import os
    
    trusted_sources = []
    try:
        with open("data/trusted_sources.json", "r") as f:
            data = json.load(f)
            trusted_sources = data.get("trusted_sources", [])
    except Exception as e:
        print(f"Error loading trusted sources: {e}")

    # Check for trusted source match or partial match (name only)
    matched_source = None
    is_trusted = False
    source_citation_missing = False
    citation_missing_warning = None

    for source in trusted_sources:
        # Check if URL is present (Strong Match)
        if source["url"] in request.text:
            matched_source = source
            is_trusted = True
            break
        
        # Check if Name is present but URL is NOT (Partial Match -> Suspicious)
        if source["name"] in request.text:
            source_citation_missing = True
            citation_missing_warning = f"Source '{source['name']}' mentioned but no valid citation found."
            # We don't break here, in case another source has a valid URL match later in the loop
            # But if we finish the loop without a URL match, this flag stays True

    # Mock score calculation
    # Ideally, we want some variation.
    score = random.randint(0, 100)
    
    verdict = "Likely Human-Written"
    
    # Overwrite verdict if suspicious citation behavior
    if source_citation_missing and not is_trusted:
        score = random.randint(80, 99) # High likelihood of fake/hallucination
        verdict = "Potential AI-Generated (Unverified Citation)"
    elif score > 50:
        verdict = "Likely AI-Generated"
    
    # Return structure matching what frontend expects


    # Load trusted facts
    trusted_facts = []
    try:
        with open("data/trusted_facts.json", "r") as f:
            data = json.load(f)
            trusted_facts = data.get("trusted_facts", [])
    except Exception as e:
        print(f"Error loading trusted facts: {e}")

    # Check for contradictions/embellishments against trusted facts
    fact_check_warning = None
    
    for fact in trusted_facts:
        # Check if topic is relevant (keyword match)
        matches = [k for k in fact["keywords"] if k in request.text.lower()]
        if matches:
            # Topic detected
            # 1. Check for Contradictions (Simple Heuristic for Demo)
            lower_text = request.text.lower()
            
            if fact["topic"] == "climate_change":
                # If text claims cooling/dropping temperatures when fact says warming/rising
                if any(x in lower_text for x in ["cooling", "dropped", "falling", "not warming", "ice age"]):
                    score = random.randint(85, 100)
                    verdict = "Potential AI-Generated (Contradicts Trusted Facts)"
                    fact_check_warning = f"Claim contradicts trusted fact from {fact['source']}: {fact['fact_statement']}"
                    break
                
                # Check for Embellishment (Numbers way higher than 1.1)
                # Very simple regex to find numbers
                import re
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", request.text)
                for num in numbers:
                    try:
                        val = float(num)
                        # If matches '10' or '20' degrees, that's embellishment
                        if val > 5 and "degree" in lower_text:
                             score = random.randint(75, 95)
                             verdict = "Potential AI-Generated (Embellishment)"
                             fact_check_warning = f"Claim embellishes magnitude. Trusted fact: {fact['fact_statement']}"
                             break
                    except:
                        pass
            
            elif fact["topic"] == "earth_shape":
                # Check for direct flat earth claims
                if "earth is flat" in lower_text or ("flat" in lower_text and "sphere" not in lower_text and "round" not in lower_text):
                     score = random.randint(90, 100)
                     verdict = "Potential AI-Generated (Scientific Contradiction)"
                     fact_check_warning = f"Claim contradicts scientific consensus from {fact['source']}: {fact['fact_statement']}"
                     break

    # Consolidate warnings
    details = {
        "word_count": word_count,
        "processing_time": "0.05s",
        "citation_warning": citation_missing_warning,
        "fact_check_warning": fact_check_warning
    }
    
    return {
        "score": score,
        "verdict": verdict,
        "trusted_source_match": is_trusted,
        "matched_source": matched_source,
        "details": details
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
