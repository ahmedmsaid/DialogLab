from huggingface_hub import snapshot_download
import os

local_dir = os.path.join(os.getcwd(), "kokoro-model")
print(f"Downloading model to {local_dir}...")

try:
    path = snapshot_download(
        repo_id="hexgrad/Kokoro-82M", 
        allow_patterns=["*.json", "*.pth", "voices/*.pt"],
        local_dir=local_dir
    )
    print(f"Download complete. Path: {path}")
    
    # Check if voices directory exists
    voices_path = os.path.join(path, "voices")
    if os.path.exists(voices_path):
        print(f"Voices directory exists at {voices_path}")
        files = os.listdir(voices_path)
        print(f"Files count: {len(files)}")
        if len(files) > 0:
            print(f"First few files: {files[:5]}")
    else:
        print(f"Voices directory MISSING at {voices_path}")
        
except Exception as e:
    print(f"Download failed: {e}")
