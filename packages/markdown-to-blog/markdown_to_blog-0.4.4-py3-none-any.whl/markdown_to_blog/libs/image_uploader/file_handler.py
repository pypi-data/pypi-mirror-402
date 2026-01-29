import os
import tempfile
import pathlib
from loguru import logger


class FileHandler:
    """파일 처리를 담당하는 클래스
    이 클래스는 파일의 존재 여부를 확인하고, 임시 파일을 생성 및 정리하는 기능을 제공합니다.
    """

    @staticmethod
    def validate_file_exists(file_path: str) -> str:
        """파일 존재 여부를 확인하고 절대 경로를 반환

        Args:
            file_path (str): 확인할 파일의 경로

        Returns:
            str: 파일의 절대 경로

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 경우
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        return str(pathlib.Path(file_path).absolute())

    @staticmethod
    def create_temp_file(extension: str = ".jpg") -> str:
        """임시 파일 생성

        Args:
            extension (str): 생성할 임시 파일의 확장자 (기본값: .jpg)

        Returns:
            str: 생성된 임시 파일의 경로
        """
        temp_file = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
        temp_path = temp_file.name
        temp_file.close()
        return temp_path

    @staticmethod
    def cleanup_temp_file(temp_path: str) -> None:
        """임시 파일 정리

        Args:
            temp_path (str): 삭제할 임시 파일의 경로
        """
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"임시 파일 삭제 완료: {temp_path}")
        except OSError as e:
            logger.warning(f"임시 파일 삭제 실패: {str(e)}")
