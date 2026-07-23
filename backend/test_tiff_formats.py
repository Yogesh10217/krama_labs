import io
from PIL import Image

def create_multiframe_tiff():
    out = io.BytesIO()
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="blue")
    img1.save(out, format="TIFF", save_all=True, append_images=[img2])
    out.seek(0)
    return out.read()

data = create_multiframe_tiff()
img = Image.open(io.BytesIO(data), formats=["TIFF", "PNG", "JPEG"])
print(f"Successfully opened BytesIO with formats! Format: {img.format}, Size: {img.size}")
