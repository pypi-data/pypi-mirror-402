from ..exceptions import ImageUploadError as BaseImageUploadError


class ImageUploadError(BaseImageUploadError):
    """이미지 업로드 중 발생하는 오류"""

    pass


class ImageDownloadError(BaseImageUploadError):
    """이미지 다운로드 중 발생하는 오류"""

    pass


class ImagePreparationError(BaseImageUploadError):
    """이미지 준비 중 발생하는 오류"""

    pass


class ServiceUnavailableError(BaseImageUploadError):
    """이미지 업로드 서비스 사용 불가 오류"""

    pass


class InvalidImageError(BaseImageUploadError):
    """유효하지 않은 이미지 파일 오류"""

    pass
