import requests
import time

def test_tts(text, description):
    print(f"\n--- Testing: {description} ---")
    print(f"Input: {text}")
    start = time.time()
    try:
        response = requests.post(
            "http://localhost:8001/tts/synthesize",
            json={
                "text": text,
                "voice": "af_heart",
                "speed": 1.0
            }
        )
        duration = time.time() - start
        if response.status_code == 200:
            print(f"Success! Time: {duration:.2f}s")
            # We could save the audio to check, but status 200 is good enough for now
            # with open(f"test_{description.replace(' ', '_')}.wav", "wb") as f:
            #     import base64
            #     f.write(base64.b64decode(response.json()['audio_wav_base64']))
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    # Test 1: Normal text
    test_tts("Hello, this is a test.", "Normal text")
    
    # Test 2: Markdown bold/italic
    test_tts("This is **bold** and *italic* text.", "Markdown emphasis")
    
    # Test 3: Code block
    test_tts("Here is code: ```print('hello')```. Did it skip?", "Code block")
    
    # Test 4: JSON-like structure
    test_tts('{"key": "value", "list": [1, 2, 3]}', "JSON artifacts")
    
    # Test 5: Links
    test_tts("Check [this link](http://google.com) out.", "Markdown link")

    # Test 6: SSML/XML tags
    test_tts("<speak>Hi <mark name='1'/>Bob—I’m <mark name='2'/>...</speak>", "SSML tags")
