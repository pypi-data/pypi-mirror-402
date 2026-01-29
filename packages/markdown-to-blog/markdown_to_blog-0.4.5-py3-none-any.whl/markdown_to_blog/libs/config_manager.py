import pathlib
from typing import Any, Dict, Optional

from configobj import ConfigObj
from loguru import logger

# 공통 설정 디렉토리
CONFIG_BASE_DIR = str(pathlib.Path.home().joinpath(".md_to_blog"))
CONFIG_FILE = str(pathlib.Path(CONFIG_BASE_DIR).joinpath("config"))
CREDENTIAL_STORAGE_PATH = str(pathlib.Path(CONFIG_BASE_DIR).joinpath("credential.storage"))
CLIENT_SECRET_PATH = str(pathlib.Path(CONFIG_BASE_DIR).joinpath("client_secret.json"))

# 설정 섹션 정의
SECTION_BLOG = "blog"
SECTION_IMAGE = "image"
SECTION_GENERAL = "general"

# 기본 설정 값
DEFAULT_CONFIG = {
    SECTION_BLOG: {
        "blog_id": "",
    },
    SECTION_IMAGE: {
        "max_retries": 3,
        "timeout_connect": 30,
        "timeout_read": 60,
        "min_file_size": 100,
        "default_service": "",  # 비어있으면 랜덤
    },
    SECTION_GENERAL: {
        "language": "ko",
        "debug": False,
    },
}


class ConfigManager:
    """통합 설정 관리 클래스"""

    _instance = None
    _config: Optional[ConfigObj] = None

    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """설정 초기화"""
        # 초기화 전에 빈 설정으로 시작
        self._config = None
        self._ensure_directories()
        self._load_config()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        config_dir = pathlib.Path(CONFIG_BASE_DIR)
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"설정 디렉토리 생성됨: {CONFIG_BASE_DIR}")

    def _load_config(self):
        """설정 파일 로드"""
        config_path = pathlib.Path(CONFIG_FILE)

        if not config_path.exists():
            logger.info("설정 파일이 없습니다. 기본 설정 파일을 생성합니다.")
            # 명시적으로 ConfigObj 인스턴스 생성
            config = ConfigObj()
            config.filename = CONFIG_FILE

            # 기본 설정 적용
            for section, values in DEFAULT_CONFIG.items():
                config[section] = {}
                for key, value in values.items():
                    config[section][key] = value # type: ignore

            config.write()
            self._config = config
        else:
            config = ConfigObj(CONFIG_FILE)

            # 누락된 설정 항목 추가
            config_updated = False
            for section, values in DEFAULT_CONFIG.items():
                if section not in config:
                    config[section] = {}
                    config_updated = True
                for key, value in values.items():
                    if key not in config[section]:
                        config[section][key] = value # type: ignore
                        config_updated = True

            if config_updated:
                config.write()

            self._config = config

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        if self._config is None:
            self._load_config()

        if self._config is None:  # 여전히 None이면 기본값 반환
            logger.warning("설정을 로드할 수 없습니다. 기본값을 사용합니다.")
            return DEFAULT_CONFIG.get(section, {}).get(key, default)

        try:
            return self._config[section][key] # type: ignore
        except (KeyError, TypeError):
            if default is not None:
                return default
            # 기본 설정 확인
            try:
                return DEFAULT_CONFIG[section][key]
            except (KeyError, TypeError):
                return None

    def set(self, section: str, key: str, value: Any) -> None:
        """설정 값 저장하기"""
        if self._config is None:
            self._load_config()

        if self._config is None:  # 여전히 None이면 새로 생성
            self._config = ConfigObj()
            self._config.filename = CONFIG_FILE

        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self._config.write()

    def get_blog_id(self) -> str:
        """블로그 ID 가져오기"""
        return str(self.get(SECTION_BLOG, "blog_id", ""))

    def set_blog_id(self, blog_id: str) -> None:
        """블로그 ID 설정하기"""
        self.set(SECTION_BLOG, "blog_id", blog_id)

    def get_image_config(self) -> Dict[str, Any]:
        """이미지 업로드 설정 가져오기"""
        max_retries = self.get(SECTION_IMAGE, "max_retries", 3)
        timeout_connect = self.get(SECTION_IMAGE, "timeout_connect", 30)
        timeout_read = self.get(SECTION_IMAGE, "timeout_read", 60)
        min_file_size = self.get(SECTION_IMAGE, "min_file_size", 100)
        default_service = self.get(SECTION_IMAGE, "default_service", "")

        return {
            "max_retries": int(max_retries) if max_retries is not None else 3,
            "timeout_connect": (int(timeout_connect) if timeout_connect is not None else 30),
            "timeout_read": int(timeout_read) if timeout_read is not None else 60,
            "min_file_size": int(min_file_size) if min_file_size is not None else 100,
            "default_service": (str(default_service) if default_service is not None else ""),
        }

    def set_image_config(self, config: Dict[str, Any]) -> None:
        """이미지 업로드 설정 설정하기"""
        for key, value in config.items():
            self.set(SECTION_IMAGE, key, value)

    def check_migrate_legacy_config(self) -> None:
        """레거시 설정 파일에서 마이그레이션"""
        legacy_config_path = str(pathlib.Path(CONFIG_BASE_DIR).joinpath("config"))

        if pathlib.Path(legacy_config_path).exists():
            try:
                legacy_config = ConfigObj(legacy_config_path)

                # 블로그 ID 마이그레이션
                if "BLOG_ID" in legacy_config:
                    self.set_blog_id(legacy_config["BLOG_ID"])
                    logger.info("레거시 블로그 ID 설정을 마이그레이션했습니다.")

                # 다른 마이그레이션 설정 추가 가능...

                # 마이그레이션 완료 후 설정 저장
                self._config.write()

            except Exception as e:
                logger.error(f"레거시 설정 마이그레이션 중 오류 발생: {e}")


# 전역 인스턴스
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """설정 관리자 인스턴스 반환"""
    return config_manager

DEFAULT_MARKDOWN_EXTRAS = ["highlightjs-lang", "fenced-code-blocks", "footnotes", "tables", "code-friendly", "smarty-pants", "metadata"]
