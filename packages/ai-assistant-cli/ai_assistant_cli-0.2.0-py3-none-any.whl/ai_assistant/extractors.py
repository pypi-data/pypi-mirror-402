import os
import base64
from io import BytesIO
from typing import Tuple
import pymupdf as fitz
from PIL import Image


def extract_text(path: str) -> Tuple[str, str | None]:
    """
    Extract content from a local file.
    Returns (content, error)
    """

    if not os.path.exists(path):
        return "", "File does not exist"

    ext = os.path.splitext(path)[1].lower()

    try:
        # ---------- PDF ----------
        if ext == ".pdf":
            text = []
            with fitz.open(path) as pdf:
                for page in pdf:
                    text.append(page.get_text())
            return "\n".join(text), None

        # ---------- IMAGE ----------
        if ext in (".jpg", ".jpeg", ".png"):
            img = Image.open(path)
            buf = BytesIO()
            img.save(buf, format="JPEG")
            encoded = base64.b64encode(buf.getvalue()).decode()
            return encoded, None

        # ---------- TEXT ----------
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(), None

    except Exception as e:
        return "", str(e)
