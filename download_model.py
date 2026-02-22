from huggingface_hub import snapshot_download
print("Downloading model...")
snapshot_download(repo_id="hexgrad/Kokoro-82M", allow_patterns=["*.json", "*.pth", "*.onnx"])
print("Download complete.")
