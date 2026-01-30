import os
from urllib.parse import quote, urlparse
from .exceptions import ImageUploadError


class URLHandler:
    """URL 처리를 담당하는 클래스
    이 클래스는 URL의 정규화, 파일 확장자 추출 및 인코딩 기능을 제공합니다.
    """

    @staticmethod
    def validate_url(url: str) -> None:
        """URL 유효성 검사

        Args:
            url (str): 검사할 URL

        Raises:
            ImageUploadError: URL이 유효하지 않을 경우
        """
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ImageUploadError(f"유효하지 않은 URL 형식입니다: {url}")
        if parsed.scheme not in ["http", "https"]:
            raise ImageUploadError(f"지원하지 않는 프로토콜입니다: {parsed.scheme}")

    @staticmethod
    def normalize_url(url: str) -> str:
        """URL 정규화

        Args:
            url (str): 정규화할 URL

        Returns:
            str: 정규화된 URL

        Raises:
            ImageUploadError: URL이 유효하지 않을 경우
        """
        # 중복된 https 프로토콜 처리
        if url.startswith("https:https://"):
            url = "https://" + url.split("https://")[-1]

        # 정규화된 URL 검증
        URLHandler.validate_url(url)
        return url

    @staticmethod
    def get_file_extension(url: str) -> str:
        """URL에서 파일 확장자 추출

        Args:
            url (str): 파일 확장자를 추출할 URL

        Returns:
            str: 추출된 파일 확장자 (기본값: .jpg)

        Raises:
            ImageUploadError: URL이 유효하지 않을 경우
        """
        URLHandler.validate_url(url)
        ext = os.path.splitext(urlparse(url).path)[1].lower()
        if ext and ext not in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            raise ImageUploadError(f"지원하지 않는 이미지 형식입니다: {ext}")
        return ext or ".jpg"

    @staticmethod
    def encode_url(url: str) -> str:
        """URL 인코딩

        Args:
            url (str): 인코딩할 URL

        Returns:
            str: 인코딩된 URL

        Raises:
            ImageUploadError: URL이 유효하지 않을 경우
        """
        URLHandler.validate_url(url)
        parsed_url = urlparse(url)
        encoded_path = quote(parsed_url.path)
        return f"{parsed_url.scheme}://{parsed_url.netloc}{encoded_path}"
