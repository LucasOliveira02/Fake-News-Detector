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
    
    # Mock score calculation
    # Ideally, we want some variation.
    # Let's just use random for true "mock" behavior as requested to determine AI vs Human
    
    score = random.randint(0, 100)
    
    verdict = "Likely Human-Written"
    if score > 50:
        verdict = "Likely AI-Generated"
    
    # Return structure matching what frontend expects
    return {
        "score": score,
        "verdict": verdict,
        "details": {
            "word_count": word_count,
            "processing_time": "0.05s"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
