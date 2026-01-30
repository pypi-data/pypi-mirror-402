"""
블로그 글 자동 생성 모듈
7단계 프로세스를 통해 SEO 최적화된 마크다운 블로그 글을 생성합니다.
"""

import os
import json
from typing import Dict, Any, List
from loguru import logger

try:
    import google.generativeai as genai
except ImportError:
    logger.error("google-generativeai 패키지가 설치되지 않았습니다. 설치해주세요: uv sync")
    genai = None


def generate_keywords(
    topic: str,
    model: str = "gemini-2.0-flash-exp",
    api_key: str = None,
) -> Dict[str, Any]:
    """
    주제를 기반으로 SEO 메인 키워드와 서브 키워드를 생성합니다.

    Args:
        topic: 블로그 글 주제
        model: 사용할 Gemini 모델 이름
        api_key: Gemini API 키 (None이면 환경 변수에서 가져옴)

    Returns:
        Dict[str, Any]: 생성된 키워드
            {
                "main_keywords": ["메인 키워드1", "메인 키워드2"],
                "sub_keywords": ["서브 키워드1", "서브 키워드2", "서브 키워드3"]
            }
    """
    if genai is None:
        raise ImportError(
            "google-generativeai 패키지가 설치되지 않았습니다. "
            "다음 명령어로 설치해주세요: uv sync"
        )

    # API 키 가져오기 (파라미터 우선, 없으면 환경 변수)
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY가 설정되지 않았습니다. "
            "다이얼로그에서 API 키를 입력하거나 환경 변수를 설정해주세요."
        )

    try:
        # Gemini API 클라이언트 초기화
        genai.configure(api_key=api_key)
        generative_model = genai.GenerativeModel(model)

        prompt = f"""다음 블로그 글 주제를 기반으로 SEO에 최적화된 키워드를 생성해주세요.

[주제]: {topic}

요구사항:
1. SEO 메인 키워드: 검색량이 높고 주제와 직접적으로 관련된 핵심 키워드 2개 생성
2. SEO 서브 키워드: 메인 키워드를 보완하는 관련 키워드 3개 생성
3. 키워드는 검색 의도에 맞게 자연스럽고 실제 사용되는 형태로 생성
4. 한국어 블로그에 적합한 키워드로 생성

다음 JSON 형식으로 응답해주세요:
{{
    "main_keywords": ["메인 키워드1", "메인 키워드2"],
    "sub_keywords": ["서브 키워드1", "서브 키워드2", "서브 키워드3"]
}}

다른 설명이나 텍스트 없이 오직 JSON 형식으로만 응답해주세요."""

        # API 호출
        logger.info("Gemini API 호출 시작 (키워드 생성)...")
        logger.debug(f"사용 모델: {model}")
        logger.debug(f"주제: {topic}")
        
        response = generative_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # API 응답 로깅
        logger.info("Gemini API 응답 수신 완료 (키워드 생성)")
        logger.debug(f"응답 텍스트 길이: {len(response_text)}자")
        logger.info(f"키워드 생성 응답:\n{response_text}")

        # JSON 코드 블록 제거
        if response_text.startswith("```"):
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

        main_keywords = result.get("main_keywords", [])
        sub_keywords = result.get("sub_keywords", [])

        # 리스트가 아닌 경우 처리
        if not isinstance(main_keywords, list):
            main_keywords = []
        if not isinstance(sub_keywords, list):
            sub_keywords = []

        logger.info(f"키워드 생성 완료: 메인={main_keywords}, 서브={sub_keywords}")

        return {
            "main_keywords": main_keywords[:2],  # 최대 2개
            "sub_keywords": sub_keywords[:3],  # 최대 3개
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        logger.error(f"응답 텍스트: {response_text}")
        raise ValueError(f"Gemini API 응답을 JSON으로 파싱할 수 없습니다: {e}")
    except Exception as e:
        logger.error(f"키워드 생성 실패: {e}")
        raise ValueError(f"키워드 생성 중 오류가 발생했습니다: {e}")


def get_default_prompt_template() -> str:
    """기본 프롬프트 템플릿을 반환합니다."""
    return """당신은 "Python + PySide6 기반 블로그 자동 생성기"를 위한 전문 글 작성 에이전트입니다.

당신의 목표는 사용자가 입력한 주제, 톤, 키워드 기반으로 최종적으로 **복붙만 하면 되는 마크다운(Markdown) 블로그 글**을 완성하는 것입니다.

[주제]: {topic}
[톤]: {tone}
[SEO 메인키워드]: {main_keywords}
[SEO 서브키워드]: {sub_keywords}

────────────────────────────────
# 1단계) 글쓰기 초안 + 문단 설계
위 입력값을 기반으로 아래 구조로 초안 작성:
1. 도입부(호기심 유발)
2. 본론 (3~4개의 소제목 + 단락 구조)
3. 결론(요약 + 행동 유도 CTA)
4. "[주제] 추가 팁" 섹션(2~3줄)

────────────────────────────────
# 2단계) 리서치·정보 취합
- 글 성향: 정보성/가이드/리뷰 중 자동 선정
- 포함 요소:
  - 특징, 장단점, 주의점
  - 최신 통계(가상 가능) & 간단한 해석
  - FAQ 2~3개
- 마지막에 "SEO 메인키워드" 포함한 H2 제목 1개 생성

────────────────────────────────
# 3단계) SEO 최적화
- 메인키워드: 제목/소제목/본문에 자연스럽게 적용
- 서브키워드: 본문에 2~3% 밀도로 삽입
- 작업 내용:
  1) 문장 자연스럽게 최적화
  2) 어떤 소제목에 어떤 키워드를 넣었는지 표시
  3) 글 마지막에 SEO 해시태그 5~7개 생성

────────────────────────────────
# 4단계) 글 교정·문체 다듬기
- 지정된 톤을 유지
- 블로그 친화적 문체로 편집
- 지나친 광고성은 제거
- 문장 가독성 강화
- 수정된 부분은 [대괄호로 표시]하지 말고 자연스럽게 통합

────────────────────────────────
# 5단계) 독창적 예시·비유 추가
- 주제 관련 구체적 사례 2~3개
- 짧은 비유 / 스토리텔링 2~3줄
- 독자가 "아하!" 할 포인트
- 마지막에 "예시로부터 얻는 팁" 1~2줄

────────────────────────────────
# 6단계) 이미지 아이디어 제작
- 글 본문에 어울리는 이미지 콘셉트 3~5개
- 각 이미지용 캡션 추가
- 무료 이미지(무저작권) 리소스 제안
- 검색용 키워드 3~5개 제공 (#해시태그)

────────────────────────────────
# 7단계) 최종 검수 및 마크다운 출력
- 전체 글 오탈자/문맥 오류 검사
- 정보·근거·사례 부족하면 보완
- CTA 문장 추가(댓글·공유·구독 등)
- 관련 링크 또는 읽으면 좋은 글 목록 제안
- 마지막에 아래 두 개 별도 섹션 제공:
  1) "SEO 키워드 적용 요약"
  2) "검수 지점 요약(3~5개)"

────────────────────────────────
# 출력 규칙
✔ 최종 출력은 **완성된 블로그 글을 마크다운(Markdown)** 형식으로 제공
✔ 최종 글을 가장 먼저 출력
✔ 그 뒤에
  - <SEO 키워드 적용 요약>
  - <검수 지점 요약>
  섹션을 분리해 출력
✔ 코드블록( ``` ) 안에 넣지 말 것
✔ 이미지 URL 등은 실제 이미지가 아니어도 됨. (가상의 예시 가능)

다음 JSON 형식으로 응답해주세요:
{{
    "markdown": "완성된 마크다운 블로그 글 전체",
    "seo_summary": "SEO 키워드 적용 요약 (어떤 소제목에 어떤 키워드를 넣었는지)",
    "review_points": ["검수 지점1", "검수 지점2", "검수 지점3", "검수 지점4", "검수 지점5"]
}}

다른 설명이나 텍스트 없이 오직 JSON 형식으로만 응답해주세요."""


def generate_blog_post(
    topic: str,
    tone: str,
    main_keywords: List[str],
    sub_keywords: List[str],
    model: str = "gemini-2.0-flash-exp",
    api_key: str = None,
    custom_prompt: str = None,
) -> Dict[str, Any]:
    """
    7단계 프로세스를 통해 블로그 글을 생성합니다.

    Args:
        topic: 블로그 글 주제
        tone: 글 톤 (친근, 전문, 유머러스, 차분)
        main_keywords: SEO 메인 키워드 (1~2개)
        sub_keywords: SEO 서브 키워드 (2~3개)
        model: 사용할 Gemini 모델 이름
        api_key: Gemini API 키 (None이면 환경 변수에서 가져옴)
        custom_prompt: 사용자 정의 프롬프트 템플릿 (None이면 기본 템플릿 사용)

    Returns:
        Dict[str, Any]: 생성된 블로그 글과 메타데이터
            {
                "markdown": "완성된 마크다운 글",
                "seo_summary": "SEO 키워드 적용 요약",
                "review_points": ["검수 지점1", "검수 지점2", ...]
            }
    """
    if genai is None:
        raise ImportError(
            "google-generativeai 패키지가 설치되지 않았습니다. "
            "다음 명령어로 설치해주세요: uv sync"
        )

    # API 키 가져오기 (파라미터 우선, 없으면 환경 변수)
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY가 설정되지 않았습니다. "
            "다이얼로그에서 API 키를 입력하거나 환경 변수를 설정해주세요."
        )

    try:
        # Gemini API 클라이언트 초기화
        genai.configure(api_key=api_key)
        generative_model = genai.GenerativeModel(model)

        # 프롬프트 템플릿 선택 (사용자 정의 또는 기본)
        prompt_template = custom_prompt if custom_prompt else get_default_prompt_template()

        # 프롬프트에 변수 치환
        prompt = prompt_template.format(
            topic=topic,
            tone=tone,
            main_keywords=', '.join(main_keywords),
            sub_keywords=', '.join(sub_keywords),
        )

        # API 호출
        logger.info("Gemini API 호출 시작 (블로그 글 생성)...")
        logger.debug(f"사용 모델: {model}")
        logger.debug(f"프롬프트 길이: {len(prompt)}자")
        logger.debug(f"주제: {topic}, 톤: {tone}")
        logger.debug(f"메인 키워드: {', '.join(main_keywords)}")
        logger.debug(f"서브 키워드: {', '.join(sub_keywords)}")
        
        response = generative_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # API 응답 로깅
        logger.info("Gemini API 응답 수신 완료 (블로그 글 생성)")
        logger.debug(f"응답 텍스트 길이: {len(response_text)}자")
        logger.info(f"블로그 글 생성 응답:\n{response_text}")

        # JSON 코드 블록 제거
        if response_text.startswith("```"):
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

        logger.info("블로그 글 생성 완료")
        return {
            "markdown": result.get("markdown", ""),
            "seo_summary": result.get("seo_summary", ""),
            "review_points": result.get("review_points", []),
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        logger.error(f"응답 텍스트: {response_text}")
        raise ValueError(f"Gemini API 응답을 JSON으로 파싱할 수 없습니다: {e}")
    except Exception as e:
        logger.error(f"블로그 글 생성 실패: {e}")
        raise ValueError(f"블로그 글 생성 중 오류가 발생했습니다: {e}")

