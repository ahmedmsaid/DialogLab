from fastapi import FastAPI
from pydantic import BaseModel
import soundfile as sf
import numpy as np
import io
import base64
import os
import huggingface_hub
import re

# Monkey patch hf_hub_download to use local files from kokoro-model directory
# This avoids issues with Hugging Face cache on Windows
original_hf_hub_download = huggingface_hub.hf_hub_download

def patched_hf_hub_download(repo_id, filename, **kwargs):
    if repo_id == "hexgrad/Kokoro-82M":
        # Check if we have a local copy in kokoro-model
        local_path = os.path.join(os.getcwd(), "kokoro-model", filename)
        if os.path.exists(local_path):
            print(f"Using local file: {local_path}")
            return local_path
        
        # Also check just relative path
        local_path_rel = os.path.join("kokoro-model", filename)
        if os.path.exists(local_path_rel):
            print(f"Using local file (rel): {local_path_rel}")
            return local_path_rel
            
        print(f"Local file not found: {local_path}, falling back to Hub")
    return original_hf_hub_download(repo_id, filename, **kwargs)

huggingface_hub.hf_hub_download = patched_hf_hub_download

from kokoro import KPipeline

def clean_text_for_tts(text: str) -> str:
    if not text:
        return ""
        
    # Remove markdown code blocks (often too verbose/technical for TTS)
    # Matches ```...``` across multiple lines
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove SSML/XML/HTML tags (e.g. <speak>, <mark name='1'/>, <break/>)
    # This matches anything starting with < and ending with >, lazy match
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove inline code marks `...`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove URLs (http/https)
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove bold/italic markers (** or *) and underscores
    text = re.sub(r'[\*_]{1,3}([^*_]+)[\*_]{1,3}', r'\1', text)
    
    # Remove remaining markdown symbols that might be pronounced
    # Remove > for blockquotes, # for headers, - for lists (if at start of line)
    text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    
    # Remove JSON-like artifacts if requested (braces, brackets)
    # The user mentioned "unnecessary things in json", implying syntax chars
    text = text.replace('{', '').replace('}', '').replace('[', '').replace(']', '').replace('\\', '')
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

class TtsRequest(BaseModel):
    text: str
    voice: str | None = None
    speed: float | None = 1.0


class TtsResponse(BaseModel):
    audio_wav_base64: str


app = FastAPI(title="Kokoro TTS Service")


pipeline = KPipeline(lang_code="a")


@app.post("/tts/synthesize", response_model=TtsResponse)
async def synthesize(req: TtsRequest) -> TtsResponse:
    cleaned_text = clean_text_for_tts(req.text)
    print(f"Original text: {req.text[:50]}...")
    print(f"Cleaned text: {cleaned_text[:50]}...")
    
    generator = pipeline(
        cleaned_text,
        voice=req.voice or "af_heart",
        speed=req.speed or 1.0,
        split_pattern=r"\n+",
    )

    audio_segments = []
    sample_rate = 24000

    for _, _, audio in generator:
        audio_segments.append(audio)

    if not audio_segments:
        raise RuntimeError("No audio generated from Kokoro pipeline")

    audio_concat = np.concatenate(audio_segments)

    buffer = io.BytesIO()
    sf.write(buffer, audio_concat, sample_rate, format="WAV")
    wav_bytes = buffer.getvalue()
    audio_b64 = base64.b64encode(wav_bytes).decode("ascii")

    return TtsResponse(audio_wav_base64=audio_b64)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

