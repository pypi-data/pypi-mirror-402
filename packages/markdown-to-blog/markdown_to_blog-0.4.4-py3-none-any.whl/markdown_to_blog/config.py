"""
설정 파일 관리를 위한 모듈입니다.
"""

from collections import OrderedDict

# 섹션 상수 정의
SECTION_GENERAL = "GENERAL"
SECTION_BLOGGER = "BLOGGER"
SECTION_IMGUR = "IMGUR"
SECTION_CLOUDINARY = "CLOUDINARY"

# 설정 기본값
DEFAULT_CONFIG = OrderedDict(
    {
        SECTION_GENERAL: {
            "language": "ko",  # 기본 언어는 한국어
            "default_image_service": "",
            "markdown_extensions": "tables,fenced_code,codehilite,nl2br",
            "codehilite_style": "rainbow_dash",
        },
        SECTION_BLOGGER: {
            "blogid": "",
            "client_id": "",
            "client_secret": "",
        },
        SECTION_IMGUR: {
            "client_id": "",
            "client_secret": "",
        },
        SECTION_CLOUDINARY: {
            "cloud_name": "",
            "api_key": "",
            "api_secret": "",
        },
    }
)

# 설정 스키마 - 각 섹션과 옵션에 대한 설명
CONFIG_SCHEMA = {
    SECTION_GENERAL: {
        "language": "UI 언어 (ko: 한국어, en: 영어)",
        "default_image_service": "기본 이미지 업로드 서비스 (imgur, cloudinary)",
        "markdown_extensions": "마크다운 변환 시 사용할 확장 기능 목록",
        "codehilite_style": "코드 하이라이팅 스타일",
    },
    SECTION_BLOGGER: {
        "blogid": "Blogger 블로그 ID",
        "client_id": "Google OAuth2 Client ID",
        "client_secret": "Google OAuth2 Client Secret",
    },
    SECTION_IMGUR: {
        "client_id": "Imgur API Client ID",
        "client_secret": "Imgur API Client Secret",
    },
    SECTION_CLOUDINARY: {
        "cloud_name": "Cloudinary Cloud Name",
        "api_key": "Cloudinary API Key",
        "api_secret": "Cloudinary API Secret",
    },
}

# 필수 설정
REQUIRED_CONFIG = {
    SECTION_BLOGGER: ["client_id", "client_secret"],
    SECTION_IMGUR: ["client_id"],
    SECTION_CLOUDINARY: ["cloud_name", "api_key", "api_secret"],
}
