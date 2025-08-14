# prepare_models.py
print("Preparing rembg models by triggering the library's own download mechanism...")

try:
    # Yeh line rembg ke apne internal downloader (Pooch) ko istemal karegi
    # taki woh model ko sahi URL se fetch kar sake.
    from rembg import new_session
    
    # Hamare ImageProcessor ko 'u2net' model chahiye.
    # Iske liye session banane se download apne aap trigger ho jayega.
    _ = new_session("u2net")
    
    print("Model preparation complete. The necessary model should now be cached.")

except Exception as e:
    print(f"An error occurred during model preparation: {e}")
    # Agar model taiyar karne me koi error aaye to build fail kar do.
    exit(1)
