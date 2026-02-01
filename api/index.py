from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random
import requests
import os
import json
import io
from PIL import Image
try:
    import numpy as np
    import cv2
    HAS_VIDEO_DEPS = True
except ImportError:
    HAS_VIDEO_DEPS = False
try:
    from pypdf import PdfReader
    import docx
    import openpyxl
    HAS_DOC_DEPS = True
except ImportError:
    HAS_DOC_DEPS = False

from dotenv import load_dotenv

load_dotenv()
api_key_status = os.environ.get("HUGGINGFACE_API_KEY")


app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for deployment variability
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
import yt_dlp
import instaloader

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

    if not text or len(text.strip()) < 5:
        return {"score": 0, "verdict": "Insufficient text for analysis"}

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
        
        tmp_img_path = None
        if image_url:
            image_input = image_url
        else:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_img:
                tmp_img.write(image_bytes)
                tmp_img_path = tmp_img.name
            image_input = tmp_img_path
            
        try:
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
        finally:
            if tmp_img_path and os.path.exists(tmp_img_path):
                os.remove(tmp_img_path)
            
    except Exception as e:
        print(f"Image Detection Error: {e}")
        return {"score": 0, "verdict": "Analysis Failed"}

def extract_frames(video_path, max_frames=5):
    """
    Extracts explicit frames from a video file.
    """
    if not HAS_VIDEO_DEPS:
        print("Video dependencies (opencv/numpy) missing. Skipping frame extraction.")
        return []
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
    target_url = request.image_url
    
    # If the URL is from Instagram, we need to extract the direct image source
    if "instagram.com" in target_url:
        try:
            loader = instaloader.Instaloader()
            # Extract the post shortcode from the URL
            if "/p/" in target_url:
                shortcode = target_url.split("/p/")[1].split("/")[0]
                post = instaloader.Post.from_shortcode(loader.context, shortcode)
                target_url = post.url
        except Exception as e:
            # Fallback to the original URL if extraction fails
            pass

    result = detect_ai_image(image_url=target_url)
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
        # Use yt-dlp to get direct URL if possible (handles TikTok, YouTube, etc.)
        # Download video to temp file using yt-dlp for robustness
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': tmp_path,
                'overwrites': True,
                'quiet': True,
                'no_warnings': True,
                'max_filesize': 50 * 1024 * 1024,  # 50MB limit
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([request.video_url])
        except Exception as e:
            print(f"yt-dlp download failed, attempting direct fetch: {e}")
            # Fallback for direct links
            try:
                r = requests.get(request.video_url, stream=True, timeout=30)
                with open(tmp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk: f.write(chunk)
            except Exception as re:
                return {"score": 0, "verdict": "Video download failed", "details": str(re)}

        
        try:
            frames = extract_frames(tmp_path)
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
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
    except Exception as e:
        print(f"Video Processing Error: {e}")
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
            # Process PDF documents by extracting text content
            try:
                reader = PdfReader(io.BytesIO(contents))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                
                # Check if the extracted text is sufficient for analysis
                if not text.strip():
                    return {"score": 0, "verdict": "No readable text found in PDF"}

                # Run text analysis on the first 2000 characters
                res = detect_ai_text(text[:2000])
                score = res["score"]
                verdict = res["verdict"]
                details = {"type": "pdf", "extracted_chars": len(text)}
            except Exception:
                return {"score": 0, "verdict": "PDF Parsing Failed"}
                
        elif "image" in content_type:
            # Analyze image bytes
            res = detect_ai_image(image_bytes=contents)
            score = res["score"]
            verdict = res["verdict"]
            details = {"type": "image"}
            
        elif "plain" in content_type or "text" in content_type:
            # Text File
            text = contents.decode("utf-8")
            res = detect_ai_text(text)
            score = res["score"]
            verdict = res["verdict"]
            details = {"type": "text_file"}
             
        elif "wordprocessingml" in content_type:
            # Word Document
            doc = docx.Document(io.BytesIO(contents))
            text = "\n".join([para.text for para in doc.paragraphs])
            res = detect_ai_text(text[:2000])
            score = res["score"]
            verdict = res["verdict"]
            details = {"type": "docx", "extracted_chars": len(text)}
            
        elif "spreadsheetml" in content_type or "excel" in content_type:
            # Excel Spreadsheet - Using openpyxl directly (lighter than pandas)
            wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
            text_data = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    for cell in row:
                        if cell is not None:
                            text_data.append(str(cell))
                    if len(text_data) > 1000: break
                if len(text_data) > 1000: break
            
            text_block = " ".join(text_data[:1000])
            res = detect_ai_text(text_block)
            score = res["score"]
            verdict = res["verdict"]
            details = {"type": "xlsx"}
            
        elif "video" in content_type:
            # Video Upload
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            
            try:
                frames = extract_frames(tmp_path)
                if not frames:
                    return {"score": 0, "verdict": "Could not extract frames from video"}
                
                scores = []
                for frame in frames:
                    res = detect_ai_image(image_bytes=frame)
                    scores.append(res['score'])
                
                avg_score = sum(scores) / len(scores) if scores else 0
                score = avg_score
                
                if score > 80: verdict = "Highly Likely Deepfake/AI Video"
                elif score > 50: verdict = "Potential Deepfake"
                else: verdict = "Likely Authentic Video"
                
                details = {"type": "video", "frames_analyzed": len(frames)}
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
             
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
