from fastapi import FastAPI
from pydantic import BaseModel
from kokoro import KPipeline
import soundfile as sf
import numpy as np
import io
import base64


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
    generator = pipeline(
        req.text,
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

