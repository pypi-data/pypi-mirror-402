"""
다국어 지원을 위한 국제화(i18n) 모듈입니다.
이 모듈은 패키지 전체에서 사용할 수 있는 메시지 번역 기능을 제공합니다.
"""

from typing import Dict, Any

from .config_manager import get_config_manager, SECTION_GENERAL


# 지원하는 언어 코드
SUPPORTED_LANGUAGES = ["ko", "en"]

# 기본 언어 코드
DEFAULT_LANGUAGE = "ko"

# 번역 메시지 사전
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ko": {
        # 일반
        "unknown_error": "알 수 없는 오류가 발생했습니다.",
        "success": "성공했습니다.",
        "failed": "실패했습니다.",
        # 설정 관련
        "config_not_found": "설정 파일을 찾을 수 없습니다.",
        "config_invalid": "설정 파일이 유효하지 않습니다.",
        # 블로그 관련
        "blog_id_set": "블로그 ID가 설정되었습니다: {}",
        "blog_id_not_set": "블로그 ID가 설정되지 않았습니다.",
        "post_published": "게시물이 발행되었습니다. Post ID: {}",
        "post_draft_saved": "게시물이 드래프트로 저장되었습니다. Post ID: {}",
        # 이미지 관련
        "image_upload_success": "이미지 업로드 성공: {}",
        "image_upload_failed": "이미지 업로드 실패: {}",
        "image_not_found": "이미지 파일을 찾을 수 없습니다: {}",
    },
    "en": {
        # 일반
        "unknown_error": "An unknown error occurred.",
        "success": "Success.",
        "failed": "Failed.",
        # 설정 관련
        "config_not_found": "Configuration file not found.",
        "config_invalid": "Configuration file is invalid.",
        # 블로그 관련
        "blog_id_set": "Blog ID has been set: {}",
        "blog_id_not_set": "Blog ID has not been set.",
        "post_published": "Post has been published. Post ID: {}",
        "post_draft_saved": "Post has been saved as draft. Post ID: {}",
        # 이미지 관련
        "image_upload_success": "Image upload successful: {}",
        "image_upload_failed": "Image upload failed: {}",
        "image_not_found": "Image file not found: {}",
    },
}


def get_current_language() -> str:
    """현재 설정된 언어 코드를 반환합니다."""
    try:
        # 설정에서 언어 코드 가져오기
        config_manager = get_config_manager()
        language = config_manager.get(SECTION_GENERAL, "language", DEFAULT_LANGUAGE)

        # 지원하는 언어인지 확인
        if language not in SUPPORTED_LANGUAGES:
            return DEFAULT_LANGUAGE

        return language
    except Exception:
        # 오류 발생 시 기본 언어 반환
        return DEFAULT_LANGUAGE


def set_language(language_code: str) -> bool:
    """
    언어 설정을 변경합니다.

    Args:
        language_code: 설정할 언어 코드

    Returns:
        bool: 성공 여부
    """
    if language_code not in SUPPORTED_LANGUAGES:
        return False

    try:
        config_manager = get_config_manager()
        config_manager.set(SECTION_GENERAL, "language", language_code)
        return True
    except Exception:
        return False


def get_message(key: str, *args: Any, **kwargs: Any) -> str:
    """
    지정된 키에 해당하는 현재 언어의 메시지를 반환합니다.

    Args:
        key: 메시지 키
        *args, **kwargs: 메시지 포맷팅에 사용할 인자

    Returns:
        str: 번역된 메시지. 키가 없는 경우 키 그대로 반환.
    """
    language = get_current_language()
    message = TRANSLATIONS.get(language, {}).get(key, key)

    try:
        # 인자가 있으면 포맷팅
        if args or kwargs:
            return message.format(*args, **kwargs)
        return message
    except Exception:
        # 포맷팅 실패 시 원본 메시지 반환
        return message


def _(key: str, *args: Any, **kwargs: Any) -> str:
    """
    get_message의 별칭 함수. 더 간결한 코드 작성을 위해 제공됩니다.

    Args:
        key: 메시지 키
        *args, **kwargs: 메시지 포맷팅에 사용할 인자

    Returns:
        str: 번역된 메시지
    """
    return get_message(key, *args, **kwargs)
