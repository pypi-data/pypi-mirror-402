"""
SwiftAPI File Upload Support.

Handles file uploads through multipart/form-data requests.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from django.core.files.storage import default_storage

from swiftapi.exceptions import ValidationError

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile
    from django.http import HttpRequest
    pass


# File field types for schemas

class FileField:
    """
    File field descriptor for schemas.

    Usage:
        class DocumentSchema(Schema):
            file: FileField = FileField(
                max_size=5 * 1024 * 1024,  # 5MB
                allowed_extensions=["pdf", "doc", "docx"],
            )
    """

    def __init__(
        self,
        *,
        max_size: int | None = None,
        allowed_extensions: list[str] | None = None,
        allowed_content_types: list[str] | None = None,
        required: bool = True,
        description: str | None = None,
    ) -> None:
        """
        Initialize file field.

        Args:
            max_size: Maximum file size in bytes
            allowed_extensions: Allowed file extensions (without dot)
            allowed_content_types: Allowed MIME types
            required: Whether the field is required
            description: Field description for docs
        """
        from swiftapi.conf import settings

        self.max_size = max_size or settings.MAX_UPLOAD_SIZE
        self.allowed_extensions = allowed_extensions or settings.ALLOWED_UPLOAD_EXTENSIONS
        self.allowed_content_types = allowed_content_types
        self.required = required
        self.description = description

    def validate(self, file: UploadedFile | None) -> UploadedFile | None:
        """
        Validate an uploaded file.

        Args:
            file: Uploaded file object

        Returns:
            Validated file

        Raises:
            ValidationError: If validation fails
        """
        if file is None:
            if self.required:
                raise ValidationError("This field is required.")
            return None

        # Check file size
        if self.max_size and file.size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            raise ValidationError(
                f"File size exceeds maximum allowed ({max_mb:.1f}MB)."
            )

        # Check extension
        if self.allowed_extensions:
            ext = self._get_extension(file.name)
            if ext.lower() not in [e.lower() for e in self.allowed_extensions]:
                raise ValidationError(
                    f"File type '{ext}' not allowed. "
                    f"Allowed: {', '.join(self.allowed_extensions)}"
                )

        # Check content type
        if self.allowed_content_types:
            content_type = file.content_type
            if content_type not in self.allowed_content_types:
                raise ValidationError(
                    f"Content type '{content_type}' not allowed."
                )

        return file

    def _get_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        if "." in filename:
            return filename.rsplit(".", 1)[1]
        return ""


class ImageField(FileField):
    """
    Image file field with image-specific validation.

    Usage:
        class ProfileSchema(Schema):
            avatar: ImageField = ImageField(
                max_size=2 * 1024 * 1024,
                max_dimensions=(1920, 1080),
            )
    """

    DEFAULT_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp"]
    DEFAULT_CONTENT_TYPES = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    def __init__(
        self,
        *,
        max_size: int | None = None,
        allowed_extensions: list[str] | None = None,
        max_dimensions: tuple[int, int] | None = None,
        min_dimensions: tuple[int, int] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize image field.

        Args:
            max_size: Maximum file size in bytes
            allowed_extensions: Allowed extensions
            max_dimensions: Maximum (width, height)
            min_dimensions: Minimum (width, height)
            **kwargs: Additional FileField arguments
        """
        super().__init__(
            max_size=max_size,
            allowed_extensions=allowed_extensions or self.DEFAULT_EXTENSIONS,
            allowed_content_types=kwargs.pop(
                "allowed_content_types",
                self.DEFAULT_CONTENT_TYPES,
            ),
            **kwargs,
        )
        self.max_dimensions = max_dimensions
        self.min_dimensions = min_dimensions

    def validate(self, file: UploadedFile | None) -> UploadedFile | None:
        """Validate image file including dimensions."""
        file = super().validate(file)

        if file is None:
            return None

        # Check dimensions if PIL is available
        try:
            from PIL import Image

            img = Image.open(file)
            width, height = img.size

            if self.max_dimensions:
                max_w, max_h = self.max_dimensions
                if width > max_w or height > max_h:
                    raise ValidationError(
                        f"Image dimensions ({width}x{height}) exceed "
                        f"maximum ({max_w}x{max_h})."
                    )

            if self.min_dimensions:
                min_w, min_h = self.min_dimensions
                if width < min_w or height < min_h:
                    raise ValidationError(
                        f"Image dimensions ({width}x{height}) are below "
                        f"minimum ({min_w}x{min_h})."
                    )

            # Reset file position
            file.seek(0)

        except ImportError:
            # PIL not available, skip dimension check
            pass

        return file


class MultipleFileField(FileField):
    """
    Multiple file upload field.

    Usage:
        class GallerySchema(Schema):
            images: MultipleFileField = MultipleFileField(
                max_files=10,
                max_size=5 * 1024 * 1024,
            )
    """

    def __init__(
        self,
        *,
        max_files: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Initialize multiple file field.

        Args:
            max_files: Maximum number of files
            **kwargs: FileField arguments
        """
        super().__init__(**kwargs)
        self.max_files = max_files

    def validate(
        self,
        files: list[UploadedFile] | None,
    ) -> list[UploadedFile] | None:
        """Validate multiple files."""
        if not files:
            if self.required:
                raise ValidationError("At least one file is required.")
            return None

        if len(files) > self.max_files:
            raise ValidationError(
                f"Maximum {self.max_files} files allowed."
            )

        validated = []
        for i, file in enumerate(files):
            try:
                validated.append(super().validate(file))
            except ValidationError as e:
                raise ValidationError(f"File {i + 1}: {e.detail}")

        return validated


# File handling utilities

class FileHandler:
    """
    Utility class for handling file uploads.
    """

    @staticmethod
    def parse_files(request: HttpRequest) -> dict[str, Any]:
        """
        Parse files from request.

        Args:
            request: HTTP request with files

        Returns:
            Dictionary of field names to file objects
        """
        return dict(request.FILES)

    @staticmethod
    def save_file(
        file: UploadedFile,
        path: str | None = None,
        storage: Any = None,
    ) -> str:
        """
        Save an uploaded file to storage.

        Args:
            file: Uploaded file
            path: Custom save path (default: generates UUID-based name)
            storage: Storage backend (default: default_storage)

        Returns:
            Path where file was saved
        """
        storage = storage or default_storage

        if path is None:
            ext = file.name.rsplit(".", 1)[-1] if "." in file.name else ""
            filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
            path = f"uploads/{filename}"

        return storage.save(path, file)

    @staticmethod
    def delete_file(path: str, storage: Any = None) -> bool:
        """
        Delete a file from storage.

        Args:
            path: File path
            storage: Storage backend

        Returns:
            True if deleted, False otherwise
        """
        storage = storage or default_storage

        if storage.exists(path):
            storage.delete(path)
            return True
        return False

    @staticmethod
    def get_file_url(path: str, storage: Any = None) -> str:
        """
        Get URL for a stored file.

        Args:
            path: File path
            storage: Storage backend

        Returns:
            Public URL for the file
        """
        storage = storage or default_storage
        return storage.url(path)


def validate_files_in_request(
    request: HttpRequest,
    file_fields: dict[str, FileField],
) -> dict[str, Any]:
    """
    Validate all files in a request against field definitions.

    Args:
        request: HTTP request
        file_fields: Dictionary of field names to FileField instances

    Returns:
        Validated files dictionary
    """
    validated = {}
    errors = {}

    for field_name, field in file_fields.items():
        file = request.FILES.get(field_name)

        try:
            validated[field_name] = field.validate(file)
        except ValidationError as e:
            errors[field_name] = [str(e.detail)]

    if errors:
        raise ValidationError(errors)

    return validated
