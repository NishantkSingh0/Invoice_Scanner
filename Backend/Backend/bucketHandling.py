from imagekitio import ImageKit
from dotenv import load_dotenv
import base64
from io import BytesIO
import os

load_dotenv()

def bucket(base64_string: str, fileName: str = "inv"):
    print("Bucket called")
    imagekit = ImageKit(
        private_key=os.getenv("IMAGEKIT_PRIVATE_KEY")
    )
    extension = "png"
    # detect mime type
    if base64_string.startswith("data:image/"):
        header = base64_string.split(";")[0]
        extension = header.split("/")[-1]
        base64_string = base64_string.split(",")[1]

    image_bytes = base64.b64decode(base64_string)
    file_object = BytesIO(image_bytes)
    final_name = f"{fileName}.{extension}"

    response = imagekit.files.upload(
        file=file_object,
        file_name=final_name,
        folder="/Invoices",
        use_unique_file_name=True
    )
    
    print("Response:", response)
    return response.url