from imagekitio import ImageKit
from dotenv import load_dotenv
import base64
from io import BytesIO
import os

load_dotenv()

def bucket(base64_string: str, fileName: str = "inv.png"):
    print("Bucket called")
    imagekit = ImageKit(
        private_key=os.getenv("IMAGEKIT_PRIVATE_KEY")
    )

    # remove header if exists
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    image_bytes = base64.b64decode(base64_string)

    file_object = BytesIO(image_bytes)

    response = imagekit.files.upload(
        file=file_object,
        file_name=fileName,
        folder="/Invoices",
        use_unique_file_name=True
    )
    print("Response: ",response)
    return response.url