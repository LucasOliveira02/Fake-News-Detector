from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random
import time
import requests
from bs4 import BeautifulSoup
import re
import os
from openai import OpenAI

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
    
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "data/trusted_sources.json"), "r") as f:
            data = json.load(f)
            source_list = data.get("trusted_sources", [])
            # Map id -> source for easy lookup
            trusted_sources_map = {s["id"]: s for s in source_list}
            trusted_sources = source_list # Keep list for existing iteration
    except Exception as e:
        print(f"Error loading trusted sources: {e}")
        trusted_sources_map = {}
        trusted_sources = []

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

    # ---------------------------------------------------------
    # Verification & Proximity Score Calculation
    # ---------------------------------------------------------
    proximity_score = None
    verification_msg = "No verification attempted"

    def get_token_set(s):
        return set(re.findall(r'\w+', s.lower()))

    def calculate_jaccard(text1, text2):
        tokens1 = get_token_set(text1)
        tokens2 = get_token_set(text2)
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return (len(intersection) / len(union)) * 100

    if is_trusted and matched_source:
        try:
            # 1. Extract the actual URL from the text
            found_urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*', request.text)
            
            target_url = None
            base_url = matched_source["url"].rstrip("/")
            for u in found_urls:
                if base_url in u:
                    target_url = u
                    break
            
            if target_url:
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(target_url, headers=headers, timeout=5)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # chunking strategy: split by paragraphs to avoid dilution
                    paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 50]
                    
                    # Method 1: LLM Verification (if key exists)
                    api_key = os.environ.get("OPENAI_API_KEY")
                    if api_key:
                        try:
                            client = OpenAI(api_key=api_key)
                            # Create a context from the first few paragraphs or best matching ones
                            # For simplicity, let's take the first 3000 chars of relevant text
                            context_text = " ".join(paragraphs)[:3000]
                            
                            prompt = f"""
                            Source Text: "{context_text}"
                            
                            User Claim: "{request.text}"
                            
                            Task: Verify if the User Claim is supported by the Source Text.
                            Return a JSON object with:
                            - score: A number between 0 and 100 indicating how well the claim is supported (100 = fully supported).
                            - reasoning: A brief explanation.
                            """
                            
                            completion = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": "You are a fact-checking assistant. Respond in JSON."},
                                    {"role": "user", "content": prompt}
                                ],
                                response_format={"type": "json_object"}
                            )
                            import json
                            result = json.loads(completion.choices[0].message.content)
                            proximity_score = result.get("score", 0)
                            verification_msg = f"AI Verified against {target_url}: {result.get('reasoning', 'No reasoning provided')}"
                            
                        except Exception as llm_ex:
                            print(f"LLM Verification failed, falling back to heuristic: {llm_ex}")
                            api_key = None # Trigger fallback

                    # Method 2: Heuristic "Best Paragraph Match" (Fallback)
                    if not api_key:
                        max_score = 0.0
                        best_chunk = ""
                        
                        # Compare user text against each paragraph individually
                        # This avoids diluting the score with the entire 1000-word article
                        for p in paragraphs:
                            score = calculate_jaccard(request.text, p)
                            if score > max_score:
                                max_score = score
                                best_chunk = p
                        
                        proximity_score = max_score
                        verification_msg = f"Verified against {target_url} (Best paragraph match)"
                        
                else:
                    verification_msg = f"Failed to fetch {target_url} (Result: {resp.status_code})"
            else:
                 verification_msg = "Trusted source matched, but specific URL could not be extracted."

        except Exception as ex:
            print(f"Verification Check Failed: {ex}")
            verification_msg = f"Error during verification: {ex}"
            
    elif source_citation_missing:
        proximity_score = 0.0
        verification_msg = "Source named but no URL provided. Cannot verify."
    # ---------------------------------------------------------
    # END: Verification & Proximity Calculation
    # ---------------------------------------------------------

    # Mock score calculation
    # Ideally, we want some variation.
    score = random.randint(0, 100)
    # uncomment this line if to test proximity_score
    # score = proximity_score if proximity_score is not None else 99
    
    verdict = "Likely Human-Written"
    
    # Overwrite verdict if suspicious citation behavior
    if source_citation_missing and not is_trusted:
        score = random.randint(80, 99) # High likelihood of fake/hallucination
        verdict = "Potential AI-Generated (Unverified Citation)"
    elif score > 50:
        verdict = "Likely AI-Generated"
    
    # Return structure matching what frontend expects


    # Load trusted facts (Claim Reviews)
    claim_reviews = []
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "data/trusted_facts.json"), "r") as f:
            data = json.load(f)
            claim_reviews = data.get("claim_reviews", [])
    except Exception as e:
        print(f"Error loading trusted facts/claims: {e}")

    # Check for contradictions/embellishments against trusted facts
    fact_check_warning = None
    
    
    for claim in claim_reviews:
        # Check if topic is relevant (keyword match)
        matches = [k for k in claim["keywords"] if k in request.text.lower()]
        
        # Get source info
        source_id = claim.get("source_id")
        source_name = trusted_sources_map.get(source_id, {}).get("name", "Unknown Source")

        # 0. Check for Direct Match / Confirmation
        # If the user text contains the Article URL OR matches the Article Content roughly
        if claim.get("source_article_url") and claim["source_article_url"] in request.text:
             is_trusted = True
             matched_source = trusted_sources_map.get(source_id)
             score = random.randint(10, 20) # Low AI score
             verdict = "Verified by Trusted Source"
             # Break early if verified? Or continue to check for contradictions? 
             # Let's say verification overrides simple checks
             break
        
        if matches:
            # Topic detected
            lower_text = request.text.lower()
            
            # 1. Check for Contradictions (Simple Heuristic for Demo)
            if claim["topic"] == "climate_change":
                # If text claims cooling/dropping temperatures when fact says warming/rising
                if any(x in lower_text for x in ["cooling", "dropped", "falling", "not warming", "ice age"]):
                    score = random.randint(85, 100)
                    verdict = "Potential AI-Generated (Contradicts Trusted Facts)"
                    fact_check_warning = f"Claim contradicts trusted fact from {source_name}: {claim['claim_reviewed']}"
                    break
                
                # Check for Embellishment (Numbers way higher than 1.1)
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", request.text)
                for num in numbers:
                    try:
                        val = float(num)
                        # If matches '10' or '20' degrees, that's embellishment
                        if val > 5 and "degree" in lower_text:
                             score = random.randint(75, 95)
                             verdict = "Potential AI-Generated (Embellishment)"
                             fact_check_warning = f"Claim embellishes magnitude. Trusted fact: {claim['claim_reviewed']}"
                             break
                    except:
                        pass
            
            elif claim["topic"] == "earth_shape":
                # Check for direct flat earth claims
                if "earth is flat" in lower_text or ("flat" in lower_text and "sphere" not in lower_text and "round" not in lower_text):
                     score = random.randint(90, 100)
                     verdict = "Potential AI-Generated (Scientific Contradiction)"
                     fact_check_warning = f"Claim contradicts scientific consensus from {source_name}: {claim['claim_reviewed']}"
                     break

            elif claim["topic"] == "spelling_strawberry":
                 # Check for incorrect '2 rs' claim
                 if "2 r" in lower_text or "two r" in lower_text:
                     score = random.randint(90, 100)
                     verdict = "Potential AI-Generated (Hallucination)"
                     fact_check_warning = f"Claim contains a common AI hallucination regarding spelling. Fact from {source_name}: {claim['claim_reviewed']}"
                     break

            elif claim["topic"] == "dietary_health":
                 # Check for 'eat rocks' recommendation
                 if "eat rocks" in lower_text or "eating rocks" in lower_text or "eat stones" in lower_text:
                     score = random.randint(95, 100)
                     verdict = "Potential AI-Generated (Dangerous Hallucination)"
                     fact_check_warning = f"Claim promotes dangerous non-food ingestion. Fact from {source_name}: {claim['claim_reviewed']}"
                     break

            elif claim["topic"] == "moon_landing":
                 # Check for 'faked' or 'hoax' claims
                 if any(x in lower_text for x in ["faked", "hoax", "staged", "not real", "studio", "kubrick"]):
                     score = random.randint(90, 100)
                     verdict = "Potential AI-Generated (Conspiracy Theory)"
                     fact_check_warning = f"Claim contradicts historical record from {source_name}: {claim['claim_reviewed']}"
                     break

    # Consolidate warnings
    details = {
        "word_count": word_count,
        "processing_time": "0.05s",
        "citation_warning": citation_missing_warning,
        "fact_check_warning": fact_check_warning,
        "proximity_score": proximity_score,
        "verification_msg": verification_msg
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
