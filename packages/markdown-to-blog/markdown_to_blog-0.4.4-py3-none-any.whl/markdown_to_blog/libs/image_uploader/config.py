from dataclasses import dataclass
from typing import Any

from ..config_manager import get_config_manager
from .exceptions import ImageUploadError


@dataclass
class UploadConfig:
    """업로드 설정을 위한 데이터 클래스
    이 데이터 클래스는 이미지 업로드에 필요한 설정을 저장합니다.

    Attributes:
        max_retries (int): 최대 재시도 횟수
        timeout_connect (int): 연결 타임아웃 시간
        timeout_read (int): 읽기 타임아웃 시간
        min_file_size (int): 최소 파일 크기
        user_agent (str): 사용자 에이전트 문자열
        default_service (str): 기본 업로드 서비스

    Raises:
        ImageUploadError: 설정 값이 유효하지 않을 경우
    """

    max_retries: int = 3
    timeout_connect: int = 30
    timeout_read: int = 60
    min_file_size: int = 100
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    default_service: str = ""

    def __post_init__(self):
        """설정 값 유효성 검사 및 전역 설정에서 값 로드"""
        # 전역 설정에서 값 로드
        self._load_from_global_config()

        # 유효성 검사
        self._validate_settings()

    def _load_from_global_config(self):
        """전역 설정에서 값 로드"""
        config_manager = get_config_manager()
        image_config = config_manager.get_image_config()

        # 설정 값이 있는 경우에만 안전하게 적용
        self._safe_set_int_value("max_retries", image_config.get("max_retries"))
        self._safe_set_int_value("timeout_connect", image_config.get("timeout_connect"))
        self._safe_set_int_value("timeout_read", image_config.get("timeout_read"))
        self._safe_set_int_value("min_file_size", image_config.get("min_file_size"))

        # 문자열 값 안전하게 적용
        default_service = image_config.get("default_service")
        if default_service is not None and isinstance(default_service, str):
            self.default_service = default_service

    def _safe_set_int_value(self, attr_name: str, value: Any) -> None:
        """정수 값을 안전하게 설정하는 헬퍼 메서드"""
        if value is not None:
            try:
                # 정수로 변환 가능한지 확인
                int_value = int(value)
                # 현재 클래스의 해당 속성에 값 설정
                setattr(self, attr_name, int_value)
            except (ValueError, TypeError):
                # 변환 불가능한 경우 무시하고 기본값 유지
                pass

    def _validate_settings(self):
        """설정 값 유효성 검사"""
        if self.max_retries < 1:
            raise ImageUploadError("최대 재시도 횟수는 1 이상이어야 합니다.")
        if self.timeout_connect < 1:
            raise ImageUploadError("연결 타임아웃은 1초 이상이어야 합니다.")
        if self.timeout_read < 1:
            raise ImageUploadError("읽기 타임아웃은 1초 이상이어야 합니다.")
        if self.min_file_size < 1:
            raise ImageUploadError("최소 파일 크기는 1바이트 이상이어야 합니다.")
        if not self.user_agent:
            raise ImageUploadError("사용자 에이전트는 비어있을 수 없습니다.")

    def save_to_global_config(self):
        """현재 설정을 전역 설정에 저장"""
        config_manager = get_config_manager()
        config = {
            "max_retries": self.max_retries,
            "timeout_connect": self.timeout_connect,
            "timeout_read": self.timeout_read,
            "min_file_size": self.min_file_size,
            "default_service": self.default_service,
        }
        config_manager.set_image_config(config)
