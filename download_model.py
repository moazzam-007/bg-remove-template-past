# download_model.py

import os
import urllib.request
from pathlib import Path

def download_model():
    """
    Downloads the u2net.onnx model required by rembg.
    """
    model_name = "u2net.onnx"
    model_url = f"https://github.com/danielgatis/rembg/releases/download/v0.0.30/{model_name}"
    
    # rembg library saves models in ~/.u2net directory
    model_dir = Path.home() / ".u2net"
    model_path = model_dir / model_name
    
    # Create the directory if it doesn't exist
    model_dir.mkdir(parents=True, exist_ok=True)
    
    if not model_path.exists():
        print(f"Downloading model from {model_url} to {model_path}...")
        try:
            urllib.request.urlretrieve(model_url, model_path)
            print("Model downloaded successfully.")
        except Exception as e:
            print(f"Error downloading model: {e}")
            # Exit with an error code to fail the build if download fails
            exit(1)
    else:
        print("Model already exists. Skipping download.")

if __name__ == "__main__":
    download_model()
