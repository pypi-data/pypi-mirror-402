import subprocess
import time
from .config import UploadConfig
from .exceptions import ImageUploadError
from .utils import log_operation
import os


class ImageDownloader:
    """이미지 다운로드를 담당하는 클래스
    이 클래스는 주어진 URL에서 이미지를 다운로드하는 기능을 제공합니다.
    """

    def __init__(self, config: UploadConfig):
        """ImageDownloader 클래스의 생성자

        Args:
            config (UploadConfig): 다운로드 설정
        """
        self.config = config

    @log_operation
    def download(self, url: str, output_path: str) -> None:
        """이미지 다운로드 실행

        Args:
            url (str): 다운로드할 이미지의 URL
            output_path (str): 다운로드한 이미지를 저장할 경로

        Raises:
            ImageUploadError: 다운로드 실패 시
        """
        curl_command = [
            "curl",
            "-L",
            "-f",
            "-S",
            "-s",
            "--connect-timeout",
            str(self.config.timeout_connect),
            "--max-time",
            str(self.config.timeout_read),
            "-A",
            self.config.user_agent,
            "-o",
            output_path,
            url,
        ]

        for attempt in range(self.config.max_retries):
            try:
                result = subprocess.run(curl_command, capture_output=True, text=True)
                if result.returncode == 0:
                    self._validate_download(output_path)
                    return

                if attempt == self.config.max_retries - 1:
                    raise ImageUploadError(f"Curl 다운로드 실패: {result.stderr}")

                time.sleep(2**attempt)
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise ImageUploadError(f"이미지 다운로드 실패: {str(e)}")

    def _validate_download(self, file_path: str) -> None:
        """다운로드된 파일 유효성 검사

        Args:
            file_path (str): 다운로드된 파일의 경로

        Raises:
            ImageUploadError: 파일 크기가 최소 크기보다 작을 경우
        """
        if os.path.getsize(file_path) < self.config.min_file_size:
            raise ImageUploadError("다운로드된 파일이 너무 작습니다")
