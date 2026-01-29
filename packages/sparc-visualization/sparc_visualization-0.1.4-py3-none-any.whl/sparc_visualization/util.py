import base64

import base64
import os
from io import BytesIO

def encode_image_to_base64(image):
    """Accept a PIL Image object or a filesystem path; return a PNG base64 string."""
    if isinstance(image, (str, os.PathLike)):
        with open(image, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    buf = BytesIO()
    image.save(buf, format="PNG", compress_level=1, optimize=False)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")