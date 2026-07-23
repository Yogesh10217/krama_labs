import os
from PIL import Image

def generate_multiframe_tiff(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Create two distinct frames
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="blue")
    
    # Save as multi-frame TIFF
    img1.save(path, format="TIFF", save_all=True, append_images=[img2])

if __name__ == "__main__":
    path = os.path.join("tests", "assets", "multiframe.tiff")
    generate_multiframe_tiff(path)
    print(f"Generated {path}")
