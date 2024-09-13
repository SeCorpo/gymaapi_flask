import os

from werkzeug.datastructures import FileStorage
from pydantic import BaseModel, Field, ValidationError

VALID_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE_MB = 5


class ImageDTO(BaseModel):
    file: FileStorage = Field(...)

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def validate_file(file: FileStorage):
        if not file:
            raise ValueError("No file provided.")

        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in VALID_EXTENSIONS:
            raise ValueError("File type is not valid.")

        file.stream.seek(0, os.SEEK_END)
        file_size_mb = file.stream.tell() / (1024 * 1024)
        file.stream.seek(0)

        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError("File size exceeds the maximum limit of 5 MB.")

        return file
