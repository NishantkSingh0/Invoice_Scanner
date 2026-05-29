from imagekitio import ImageKit
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import base64
import os

load_dotenv()


def compress_image(base64_string: str, max_width: int = 1500, quality: int = 85):
    """
    Compress image while preserving OCR readability.
    Returns BytesIO object ready for upload.
    """

    image_bytes = base64.b64decode(base64_string)

    img = Image.open(BytesIO(image_bytes))

    # Convert transparent images to RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Resize only if image is too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)

        img = img.resize(
            (max_width, new_height),
            Image.LANCZOS
        )

    output = BytesIO()

    img.save(
        output,
        format="JPEG",
        quality=quality,
        optimize=True
    )

    output.seek(0)

    return output


def bucket(base64_string: str, file_name: str = "inv"):
    print("Bucket called")

    imagekit = ImageKit(
        private_key=os.getenv("IMAGEKIT_PRIVATE_KEY")
    )

    # Remove Base64 Header
    if base64_string.startswith("data:image/"):
        base64_string = base64_string.split(",", 1)[1]

    # Compress image
    compressed_file = compress_image(
        base64_string,
        max_width=1500,
        quality=85
    )

    response = imagekit.files.upload(
        file=compressed_file,
        file_name=f"{file_name}.jpg",
        folder="/inv",
        use_unique_file_name=True
    )

    print("Response:", response)

    return response.url