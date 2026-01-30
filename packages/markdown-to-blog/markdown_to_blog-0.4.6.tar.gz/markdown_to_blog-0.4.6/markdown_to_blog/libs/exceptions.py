"""
마크다운 투 블로그 패키지의 공통 예외 클래스 모듈입니다.
이 모듈은 패키지 전체에서 사용할 수 있는 표준화된 예외 클래스를 제공합니다.
"""


class MdBlogError(Exception):
    """마크다운 투 블로그의 기본 예외 클래스"""

    def __init__(self, message: str = "Unknown error occurred", *args):
        self.message = message
        super().__init__(message, *args)

    def __str__(self) -> str:
        return self.message


class ConfigError(MdBlogError):
    """설정 관련 오류"""

    pass


class AuthError(MdBlogError):
    """인증 관련 오류"""

    pass


class BlogError(MdBlogError):
    """블로그 관련 오류"""

    pass


class ConversionError(MdBlogError):
    """변환 관련 오류"""

    pass


class PublishError(MdBlogError):
    """발행 관련 오류"""

    pass


class ImageError(MdBlogError):
    """이미지 처리 관련 오류"""

    pass


class ImageUploadError(ImageError):
    """이미지 업로드 관련 오류"""

    pass


class ImageDownloadError(ImageError):
    """이미지 다운로드 관련 오류"""

    pass


class NetworkError(MdBlogError):
    """네트워크 관련 오류"""

    pass


class ValidationError(MdBlogError):
    """검증 관련 오류"""

    pass


class FileError(MdBlogError):
    """파일 처리 관련 오류"""

    pass
