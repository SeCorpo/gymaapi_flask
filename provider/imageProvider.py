import logging
import os
import random
import string
from io import BytesIO
from shutil import move
from typing import Optional
from PIL import Image

from dto.imageDTO import ImageDTO

# Define image paths from environment variables or defaults
LARGE_IMAGE_PATH = os.getenv("LARGE_IMAGE_PATH", "images/large")
MEDIUM_IMAGE_PATH = os.getenv("MEDIUM_IMAGE_PATH", "images/medium")
ARCHIVE_PATH = os.getenv("ARCHIVE_PATH", "images/archive")

# Ensure storage paths exist
os.makedirs(LARGE_IMAGE_PATH, exist_ok=True)
os.makedirs(MEDIUM_IMAGE_PATH, exist_ok=True)
os.makedirs(ARCHIVE_PATH, exist_ok=True)


def process_image(image_dto: ImageDTO) -> Optional[dict]:
    """Process the uploaded image file, create two resized versions (large and medium) and return their paths."""
    try:
        # Open the uploaded image file
        file_to_image = Image.open(image_dto.file.file)

        # Create large image (1000x1000, max 150kb)
        large_image = resize_and_crop_image(file_to_image, (1000, 1000), 150)
        pf_path_l = store_image(large_image, generate_random_filename('l', LARGE_IMAGE_PATH), LARGE_IMAGE_PATH)

        # Create medium image (200x200, max 50kb)
        medium_image = resize_and_crop_image(file_to_image, (200, 200), 50)
        pf_path_m = store_image(medium_image, generate_random_filename('m', MEDIUM_IMAGE_PATH), MEDIUM_IMAGE_PATH)

        return {'pf_path_l': pf_path_l, 'pf_path_m': pf_path_m}
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return None


def resize_and_crop_image(image: Image, resolution: tuple[int, int], file_size_kb: int) -> Image:
    """Resize and crop the image to a square, then compress to a target file size."""
    try:
        image = image.convert('RGB')  # Ensure the image is in RGB format

        # Crop the image to a centered square
        width, height = image.size
        min_dimension = min(width, height)
        left = (width - min_dimension) / 2
        top = (height - min_dimension) / 2
        right = (width + min_dimension) / 2
        bottom = (height + min_dimension) / 2

        image = image.crop((left, top, right, bottom))
        image.thumbnail(resolution)  # Resize to target resolution

        # Compress image to fit within the file size limit
        buffer = BytesIO()
        quality = 95
        while True:
            buffer.seek(0)
            buffer.truncate()
            image.save(buffer, format='JPEG', quality=quality)
            size_kb = buffer.tell() / 1024

            if size_kb <= file_size_kb or quality <= 10:
                break
            quality -= 5

        buffer.seek(0)
        return Image.open(buffer)
    except Exception as e:
        logging.error(f"Error resizing image: {e}")
        raise


def store_image(image: Image, file_name: str, location: str) -> str:
    """Save the image to a specified location and return the file name."""
    try:
        file_path = os.path.join(location, file_name)
        image.save(file_path, format='JPEG')
        return file_name
    except Exception as e:
        logging.error(f"Error storing image: {e}")
        raise


def generate_random_filename(prefix: str, path: str) -> str:
    """Generate a unique random filename with the given prefix and ensure it doesn't already exist."""
    while True:
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        file_name = f"{prefix}_{random_str}.jpg"
        if not os.path.exists(os.path.join(path, file_name)):
            return file_name


def move_images_to_archive(pf_name_l: str, pf_name_m: str) -> bool:
    """Move the large and medium images to the archive directory."""
    try:
        pf_path_l = os.path.join(LARGE_IMAGE_PATH, pf_name_l)
        pf_path_m = os.path.join(MEDIUM_IMAGE_PATH, pf_name_m)

        new_path_l = os.path.join(ARCHIVE_PATH, os.path.basename(pf_path_l))
        new_path_m = os.path.join(ARCHIVE_PATH, os.path.basename(pf_path_m))

        move(pf_path_l, new_path_l)
        move(pf_path_m, new_path_m)

        logging.info(f"Moved {pf_path_l} to {new_path_l}")
        logging.info(f"Moved {pf_path_m} to {new_path_m}")
        return True
    except Exception as e:
        logging.error(f"Error moving images to archive: {e}")
        return False
