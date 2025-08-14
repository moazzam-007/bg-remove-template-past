# download_model.py

import os
import urllib.request
from pathlib import Path

def download_model():
    """
    Downloads the u2net.onnx model required by rembg.
    """
    model_name = "u2net.onnx"
    # NEECHE DIYA GAYA URL UPDATE KAR DIYA GAYA HAI
    model_url = f"https://github.com/danielgatis/rembg/releases/download/v2.0.54/{model_name}"
    
    # rembg library models ko ~/.u2net directory me save karti hai
    model_dir = Path.home() / ".u2net"
    model_path = model_dir / model_name
    
    # Agar directory nahi hai to banayein
    model_dir.mkdir(parents=True, exist_ok=True)
    
    if not model_path.exists():
        print(f"Downloading model from {model_url} to {model_path}...")
        try:
            urllib.request.urlretrieve(model_url, model_path)
            print("Model downloaded successfully.")
        except Exception as e:
            print(f"Error downloading model: {e}")
            # Agar download fail ho to build ko fail kar dein
            exit(1)
    else:
        print("Model already exists. Skipping download.")

if __name__ == "__main__":
    download_model()
