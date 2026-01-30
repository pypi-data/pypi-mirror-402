from typing import Optional
from .config import UploadConfig
from .exceptions import ImageUploadError
from .file_handler import FileHandler
from .url_handler import URLHandler
from .image_downloader import ImageDownloader
from .image_upload_service import DefaultImageUploader
from .utils import log_operation


class ImageUploader:
    """이미지 업로드를 관리하는 메인 클래스
    이 클래스는 이미지 업로드의 전체 과정을 관리합니다.
    """

    def __init__(
        self,
        config: Optional[UploadConfig] = None,
        service: Optional[str] = None,
        use_tui: bool = False,
    ):
        """ImageUploader 클래스의 생성자

        Args:
            config (Optional[UploadConfig]): 업로드 설정
            service (Optional[str]): 사용할 특정 업로드 서비스
            use_tui (bool): TUI 모드 사용 여부
        """
        self.config = config or UploadConfig()
        self.file_handler = FileHandler()
        self.url_handler = URLHandler()
        self.downloader = ImageDownloader(self.config)
        self.uploader = DefaultImageUploader(service, use_tui)

    @log_operation
    def upload(self, source: str) -> str:
        """이미지 업로드 실행

        Args:
            source (str): 업로드할 이미지의 경로 또는 URL

        Returns:
            str: 업로드된 이미지의 URL

        Raises:
            ImageUploadError: 소스가 비어있거나 업로드 실패 시
        """
        if not source:
            raise ImageUploadError("소스가 비어있습니다.")

        # URL 여부 확인 (http 또는 https로 시작하는 경우만 URL로 처리)
        is_url = source.lower().startswith(("http://", "https://"))
        return (
            self._upload_from_url(source) if is_url else self._upload_from_file(source)
        )

    def _upload_from_file(self, file_path: str) -> str:
        """파일에서 직접 업로드

        Args:
            file_path (str): 업로드할 이미지 파일의 경로

        Returns:
            str: 업로드된 이미지의 URL
        """
        absolute_path = self.file_handler.validate_file_exists(file_path)
        return self.uploader.upload(absolute_path)

    def _upload_from_url(self, url: str) -> str:
        """URL에서 이미지를 다운로드하고 업로드

        Args:
            url (str): 다운로드할 이미지의 URL

        Returns:
            str: 업로드된 이미지의 URL
        """
        encoded_url = self.url_handler.encode_url(url)
        extension = self.url_handler.get_file_extension(url)
        temp_path = self.file_handler.create_temp_file(extension)

        try:
            self.downloader.download(encoded_url, temp_path)
            return self.uploader.upload(temp_path)
        finally:
            self.file_handler.cleanup_temp_file(temp_path)
