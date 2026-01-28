from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random
import requests
import os
import json
import io
from PIL import Image
import numpy as np
import cv2
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
api_key_status = os.environ.get("HUGGINGFACE_API_KEY")


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

class ImageRequest(BaseModel):
    image_url: str

class VideoRequest(BaseModel):
    video_url: str

@app.get("/")
def read_root():
    return {"message": "AI Content Detector API is running"}

# ---------------------------------------------------------
# Helper Functions for Detection
# ---------------------------------------------------------

import time
from huggingface_hub import InferenceClient

def detect_ai_text(text: str):
    """
    Detects if text is AI-generated using Zero-Shot Classification.
    Model: facebook/bart-large-mnli
    """
    api_key = os.environ.get("HUGGINGFACE_API_KEY")
    score = 0
    verdict = "Analysis Unavailable (Missing Key)"
    
    if not api_key:
        return {"score": 0, "verdict": "Likely Human (Dev Mode - No API Key)"}

    client = InferenceClient(token=api_key, timeout=30)
    # Using a faster DistilBART model
    model_id = "valhalla/distilbart-mnli-12-3"
    
    try:
        # Zero-Shot Classification allows us to define arbitrary labels
        # We classify the text into "AI Generated" or "Human Written"
        labels = ["AI Generated", "Human Written"]
        result = client.zero_shot_classification(text[:1000], labels, model=model_id)

        
        # Result is a list of objects, e.g. [ZeroShotClassificationOutputElement(label='AI Generated', score=0.9), ...]
        ai_score = 0
        
        # Handle list of objects (latest huggingface_hub version)
        if isinstance(result, list):
            for r in result:
                if r.label == "AI Generated":
                    ai_score = r.score * 100
        else:
            # Fallback for older versions/different return shapes
            for i, label in enumerate(result.labels):
                 if label == "AI Generated":
                    ai_score = result.scores[i] * 100
        
        score = ai_score
        if score > 80: verdict = "Highly Likely AI-Generated"
        elif score > 50: verdict = "Likely AI-Generated"
        else: verdict = "Likely Human-Written"
        
        return {"score": score, "verdict": verdict}
            
    except Exception as e:
        print(f"Text Detection Error: {e}")
        return {"score": 0, "verdict": f"Analysis Failed: {str(e)}"}

def detect_ai_image(image_url: str = None, image_bytes: bytes = None):
    """
    Detects if an image is AI-generated using InferenceClient.
    Model: umereq/ai-image-detector
    """
    api_key = os.environ.get("HUGGINGFACE_API_KEY")
    if not api_key:
        return {"score": 0, "verdict": "Likely Real (Dev Mode - No API Key)"}

    client = InferenceClient(token=api_key, timeout=30)
    model_id = "umm-maybe/AI-image-detector"
    
    try:
        # We need to pass URL or bytes. InferenceClient supports image_classification with url/file.
        # But for bytes, we might need to wrap in BytesIO or pass as data.
        # However, client.image_classification handles URL string automatically.
        
        if image_url:
            image_input = image_url
        else:
            image_input = io.BytesIO(image_bytes)
            
        results = client.image_classification(image_input, model=model_id)
        
        # Results is list of ClassLabel (score, label)
        ai_prob = 0
        
        for r in results:
            # dima806 model usually returns labels like 'Real' or 'Fake'
            if r.label.lower() in ['artificial', 'ai', 'fake']:
                ai_prob = r.score * 100
        
        if ai_prob > 85: verdict = "Highly Likely AI-Generated"
        elif ai_prob > 50: verdict = "Likely AI-Generated"
        else: verdict = "Likely Real Image"
        
        return {"score": ai_prob, "verdict": verdict}
            
    except Exception as e:
        print(f"Image Detection Error: {e}")
        return {"score": 0, "verdict": "Analysis Failed"}

def extract_frames(video_path, max_frames=5):
    """
    Extracts explicit frames from a video file.
    """
    frames = []
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0: return []
        
        # Pick 5 evenly spaced frames
        indices = np.linspace(0, total_frames-1, max_frames, dtype=int)
        
        for i in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                # Convert to bytes for API
                is_success, buffer = cv2.imencode(".jpg", frame)
                if is_success:
                    frames.append(buffer.tobytes())
        cap.release()
    except Exception as e:
        print(f"Frame Extraction Error: {e}")
    return frames

# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@app.post("/detect/text")
async def analyze_text(request: TextRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    result = detect_ai_text(request.text)
    
    return {
        "score": result["score"],
        "verdict": result["verdict"],
        "details": {
            "char_count": len(request.text),
            "model": "valhalla/distilbart-mnli-12-3"
        }
    }

@app.post("/detect/image")
async def analyze_image(request: ImageRequest):
    result = detect_ai_image(image_url=request.image_url)
    return {
        "score": result["score"],
        "verdict": result["verdict"],
        "details": {
            "source": "url",
            "model": "umm-maybe/AI-image-detector"
        }
    }

@app.post("/detect/video")
async def analyze_video(request: VideoRequest):
    # For a URL, efficiently extracting frames is hard without downloading.
    # We will attempt to download a small portion or the whole file to temp.
    try:
        # Download video to temp file
        import tempfile
        
        # Check size (head request)
        head = requests.head(request.video_url)
        content_length = int(head.headers.get('content-length', 0))
        if content_length > 50 * 1024 * 1024: # 50MB limit
             return {"score": 0, "verdict": "Video too large for analysis"}

        r = requests.get(request.video_url, stream=True)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk: tmp.write(chunk)
            tmp_path = tmp.name
        
        frames = extract_frames(tmp_path)
        os.remove(tmp_path) # Cleanup
        
        if not frames:
             return {"score": 0, "verdict": "Could not extract frames"}
        
        # Analyze frames
        scores = []
        for frame in frames:
             res = detect_ai_image(image_bytes=frame)
             scores.append(res['score'])
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score > 80: verdict = "Highly Likely Deepfake/AI Video"
        elif avg_score > 50: verdict = "Potential Deepfake"
        else: verdict = "Likely Authentic Video"

        return {
            "score": avg_score,
            "verdict": verdict,
            "details": {
                "frames_analyzed": len(frames),
                "model": "Frame-by-Frame Analysis"
            }
        }
        
    except Exception as e:
        print(f"Video Video Error: {e}")
        return {"score": 0, "verdict": "Video Processing Failed", "error": str(e)}

@app.post("/detect/file")
async def analyze_file(file: UploadFile = File(...)):
    content_type = file.content_type
    
    score = 0
    verdict = "Unknown File Type"
    details = {}
    
    try:
        contents = await file.read()
        
        if "pdf" in content_type:
            # Extract text from PDF
            try:
                reader = PdfReader(io.BytesIO(contents))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                
                # Analyze text
                res = detect_ai_text(text[:2000]) # Limit
                score = res["score"]
                verdict = res["verdict"]
                details = {"type": "pdf", "extracted_chars": len(text)}
            except Exception as e:
                return {"score": 0, "verdict": "PDF Parsing Failed"}
                
        elif "image" in content_type:
            # Analyze image bytes
            res = detect_ai_image(image_bytes=contents)
            score = res["score"]
            verdict = res["verdict"]
            details = {"type": "image"}
            
        elif "text" in content_type:
             text = contents.decode("utf-8")
             res = detect_ai_text(text)
             score = res["score"]
             verdict = res["verdict"]
             details = {"type": "text_file"}
             
    except Exception as e:
        return {"score": 0, "verdict": f"File Error: {str(e)}"}

    return {
        "score": score,
        "verdict": verdict,
        "details": details
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
