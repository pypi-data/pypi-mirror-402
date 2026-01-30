"""
Gemini API를 사용하여 마크다운 내용에서 키워드와 요약을 추출하는 모듈입니다.
"""

import os
import json
from typing import Dict, Any
from loguru import logger

try:
    import google.generativeai as genai
except ImportError:
    logger.error("google-generativeai 패키지가 설치되지 않았습니다. 설치해주세요: uv sync")
    genai = None


def extract_keywords_and_summary(markdown_content: str, model: str = "gemini-pro") -> Dict[str, Any]:
    """
    Gemini API를 사용하여 마크다운 내용에서 주요 키워드와 한줄 요약을 추출합니다.

    Args:
        markdown_content (str): 마크다운 파일의 내용
        model (str): 사용할 Gemini 모델 이름 (기본값: "gemini-pro")

    Returns:
        Dict[str, any]: 다음 형식의 딕셔너리
            {
                "keywords": ["키워드1", "키워드2", ...],
                "description": "한줄 요약"
            }

    Raises:
        ValueError: Gemini API 키가 설정되지 않았거나 API 호출 실패 시
    """
    if genai is None:
        raise ImportError(
            "google-generativeai 패키지가 설치되지 않았습니다. "
            "다음 명령어로 설치해주세요: uv sync"
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. "
            "환경 변수를 설정하거나 다음 명령어로 설정해주세요: "
            "export GEMINI_API_KEY=your_api_key"
        )

    try:
        # Gemini API 클라이언트 초기화
        genai.configure(api_key=api_key)

        # 모델 선택
        generative_model = genai.GenerativeModel(model)

        # 프롬프트 작성
        prompt = f"""다음 마크다운 문서를 분석하여 다음 형식의 JSON으로 응답해주세요:

{{
    "keywords": ["주요 키워드1", "주요 키워드2", "주요 키워드3", "주요 키워드4", "주요 키워드5"],
    "description": "문서의 핵심 내용을 한 문장으로 요약한 설명"
}}

요구사항:
- keywords는 문서의 핵심 주제를 나타내는 키워드를 5개까지 추출하세요
- description은 검색 엔진 최적화(SEO)를 위한 한 줄 요약으로, 150자 이내로 작성하세요
- 다른 설명이나 텍스트 없이 오직 JSON 형식으로만 응답해주세요

마크다운 내용:
{markdown_content}"""

        # API 호출
        response = generative_model.generate_content(prompt)

        # 응답 텍스트 추출
        response_text = response.text.strip()

        # JSON 코드 블록 제거 (```json ... ``` 형식 처리)
        if response_text.startswith("```"):
            # 코드 블록 시작/끝 찾기
            lines = response_text.split("\n")
            json_lines = []
            in_json_block = False
            for line in lines:
                if line.strip().startswith("```json") or line.strip().startswith("```"):
                    in_json_block = True
                    continue
                if line.strip() == "```" and in_json_block:
                    break
                if in_json_block:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        # JSON 파싱
        result = json.loads(response_text)

        # 결과 검증 및 반환
        keywords = result.get("keywords", [])
        description = result.get("description", "")

        # keywords가 리스트가 아닌 경우 처리
        if not isinstance(keywords, list):
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(",")]
            else:
                keywords = []

        logger.info(f"키워드 추출 완료: {keywords}")
        logger.info(f"요약 생성 완료: {description}")

        return {
            "keywords": keywords[:5],  # 최대 5개만 반환
            "description": description[:150] if description else "",  # 최대 150자
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        logger.error(f"응답 텍스트: {response_text}")
        raise ValueError(f"Gemini API 응답을 JSON으로 파싱할 수 없습니다: {e}")
    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        raise ValueError(f"Gemini API 호출 중 오류가 발생했습니다: {e}")

