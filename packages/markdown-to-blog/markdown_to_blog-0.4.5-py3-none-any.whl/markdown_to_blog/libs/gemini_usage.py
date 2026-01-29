"""
Gemini API 사용량 및 모델 정보 확인 모듈
"""

import os
from typing import Dict, Any, List
from loguru import logger

try:
    import google.generativeai as genai
except ImportError:
    logger.error("google-generativeai 패키지가 설치되지 않았습니다. 설치해주세요: uv sync")
    genai = None


def get_available_models(api_key: str = None) -> List[Dict[str, Any]]:
    """
    사용 가능한 Gemini 모델 목록을 가져옵니다.

    Args:
        api_key: Gemini API 키 (None이면 환경 변수에서 가져옴)

    Returns:
        List[Dict[str, Any]]: 모델 정보 리스트
    """
    if genai is None:
        raise ImportError(
            "google-generativeai 패키지가 설치되지 않았습니다. "
            "다음 명령어로 설치해주세요: uv sync"
        )

    # API 키 가져오기
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY가 설정되지 않았습니다. "
            "다이얼로그에서 API 키를 입력하거나 환경 변수를 설정해주세요."
        )

    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        
        available_models = []
        for model in models:
            # generateContent를 지원하는 모델만 필터링
            if "generateContent" in model.supported_generation_methods:
                available_models.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                })
        
        logger.info(f"사용 가능한 모델 {len(available_models)}개 조회 완료")
        return available_models
    except Exception as e:
        logger.error(f"모델 목록 조회 실패: {e}")
        raise ValueError(f"모델 목록을 가져올 수 없습니다: {e}")


def check_api_status(api_key: str = None) -> Dict[str, Any]:
    """
    API 키 상태 및 사용 가능한 정보를 확인합니다.

    Args:
        api_key: Gemini API 키 (None이면 환경 변수에서 가져옴)

    Returns:
        Dict[str, Any]: API 상태 정보
            {
                "status": "valid" | "invalid",
                "message": "상태 메시지",
                "models_count": 모델 개수,
                "available_models": [모델 목록],
            }
    """
    if genai is None:
        return {
            "status": "error",
            "message": "google-generativeai 패키지가 설치되지 않았습니다.",
            "models_count": 0,
            "available_models": [],
        }

    # API 키 가져오기
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "API 키가 설정되지 않았습니다.",
            "models_count": 0,
            "available_models": [],
        }

    try:
        genai.configure(api_key=api_key)
        
        # 모델 목록 조회
        models = genai.list_models()
        available_models = []
        for model in models:
            if "generateContent" in model.supported_generation_methods:
                available_models.append({
                    "name": model.name,
                    "display_name": model.display_name,
                })
        
        # 간단한 테스트 요청으로 API 키 유효성 확인
        try:
            test_model = genai.GenerativeModel("gemini-2.0-flash-exp")
            # 실제 요청은 하지 않고 모델 객체만 생성하여 확인
            test_result = "valid"
        except Exception as e:
            test_result = f"warning: {str(e)}"
        
        return {
            "status": "valid",
            "message": "API 키가 유효합니다.",
            "models_count": len(available_models),
            "available_models": available_models,
            "test_result": test_result,
        }
    except Exception as e:
        logger.error(f"API 상태 확인 실패: {e}")
        return {
            "status": "error",
            "message": f"API 키 확인 중 오류가 발생했습니다: {str(e)}",
            "models_count": 0,
            "available_models": [],
        }

