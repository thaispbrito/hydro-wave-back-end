import os
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUD_NAME'),
    api_key=os.getenv('CLOUD_API_KEY'),
    api_secret=os.getenv('CLOUD_API_SECRET'),
    secure=True
)

# Image upload
def upload_image(file):
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]