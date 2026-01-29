"""
AirTable rowid 기반 마크다운 포스트 생성 유틸리티.

이 모듈은 CLI/스크립트에서 재사용하기 위해, 핵심 로직을 순수 함수 형태로 제공합니다.

파이프라인:
1) Airtable 레코드 조회 → fields에서 url/summary 추출
2) Custom API(/v1/chat/completions)로 summary를 블로그 글(content) + description + keywords(4개)로 변환
3) Custom API로 title 생성(실패 시 rule fallback)
4) thumbnail_maker로 썸네일 생성 후 출력에서 URL 파싱
5) 최종 마크다운 생성 후 `<rowid>.md` 저장
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import requests


class GenerateMarkdownError(RuntimeError):
    """생성 파이프라인 실패 시 발생."""


@dataclass(frozen=True)
class ContentPack:
    """LLM 변환 결과 묶음."""

    content: str
    description: str
    keywords: list[str]


def _silence_loguru() -> None:
    """
    일부 모듈(예: airtable_getrow)이 loguru를 stdout에 출력할 수 있어,
    기본 동작은 조용히(성공 시 출력 없음) 유지하도록 무력화합니다.
    """

    try:
        from loguru import logger  # type: ignore

        logger.remove()
        logger.add(lambda _: None)
    except Exception:
        pass


def _find_repo_root(start: Path) -> Path | None:
    """상위로 올라가며 pyproject.toml이 있는 디렉토리를 repo root로 간주합니다."""

    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists():
            return p
    return None


def _load_dotenv_if_present() -> None:
    """
    `.env`를 가능한 위치에서 로드합니다.
    - 우선순위: 현재 작업 디렉토리 → repo root → (없으면 skip)
    """

    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(dotenv_path=cwd_env)
        return

    root = _find_repo_root(Path.cwd())
    if root is not None:
        root_env = root / ".env"
        if root_env.exists():
            load_dotenv(dotenv_path=root_env)


def get_custom_api_base_url() -> str:
    """
    Custom API 접속 URL을 결정합니다.

    우선순위:
    1) CUSTOM_API_BASE_URL (예: http://127.0.0.1:8001)
    2) CUSTOM_API_HOST (+ CUSTOM_API_PORT, 기본 8001)
       - CUSTOM_API_HOST에 scheme이 없으면 http://로 가정
       - CUSTOM_API_HOST에 이미 :port가 포함되어 있으면 그대로 사용
    """

    _load_dotenv_if_present()

    base_url = (os.getenv("CUSTOM_API_BASE_URL") or "").strip()
    if base_url:
        return base_url.rstrip("/")

    host = (os.getenv("CUSTOM_API_HOST") or "").strip()
    if not host:
        return "http://127.0.0.1:8001"

    if not re.match(r"^https?://", host, flags=re.IGNORECASE):
        host = f"http://{host}"

    if re.match(r"^https?://[^/]+:\d+($|/)", host, flags=re.IGNORECASE):
        return host.rstrip("/")

    port = (os.getenv("CUSTOM_API_PORT") or "8001").strip() or "8001"
    host_only = host.split("/", 3)[:3]
    if len(host_only) >= 3:
        scheme = host_only[0]
        netloc = host_only[2]
        return f"{scheme}//{netloc}:{port}".rstrip("/")

    return host.rstrip("/")


def get_custom_api_key() -> str | None:
    """`.env`의 CUSTOM_API_KEY를 읽어 `X-API-Key` 값으로 사용합니다."""

    _load_dotenv_if_present()
    key = os.getenv("CUSTOM_API_KEY")
    return key.strip() if isinstance(key, str) and key.strip() else None


def get_custom_api_timeout() -> float:
    _load_dotenv_if_present()
    timeout_raw = (os.getenv("CUSTOM_API_TIMEOUT") or "60").strip()
    try:
        return float(timeout_raw)
    except ValueError:
        return 60.0


def _compact_ws(text: str) -> str:
    """여러 공백/개행을 한 칸으로 정규화합니다."""

    return " ".join(str(text).split()).strip()


def _escape_html_attr(value: str) -> str:
    """meta tag attribute에 넣을 문자열을 안전하게 escape 합니다."""

    v = str(value).replace("\r", " ").replace("\n", " ").strip()
    v = (
        v.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return v


def _extract_first_json_object(text: str) -> str:
    """
    LLM 응답에 코드펜스/여분 텍스트가 섞여도 첫 JSON object를 뽑아냅니다.
    """

    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        return s

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
    if fenced:
        inner = fenced.group(1).strip()
        if inner.startswith("{") and inner.endswith("}"):
            return inner

    m = re.search(r"\{[\s\S]*\}", s)
    if not m:
        raise ValueError("LLM 응답에서 JSON 객체를 찾을 수 없습니다.")
    return m.group(0)


def parse_json_response(text: str) -> dict[str, Any]:
    """LLM 텍스트 응답에서 JSON object(dict)를 최대한 견고하게 파싱합니다."""

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    obj = _extract_first_json_object(text)
    data2 = json.loads(obj)
    if not isinstance(data2, dict):
        raise ValueError("LLM JSON 응답이 object(dict)가 아닙니다.")
    return data2


def _coerce_keywords(raw: Any) -> list[str]:
    """keywords를 4개 list[str]로 정규화합니다."""

    items: list[str] = []
    if isinstance(raw, list):
        for x in raw:
            t = _compact_ws(x)
            if t:
                items.append(t)
    else:
        s = _compact_ws(raw)
        if s:
            parts = re.split(r"[,\n]+", s)
            items = [p.strip() for p in parts if p.strip()]

    deduped: list[str] = []
    seen = set()
    for it in items:
        if it not in seen:
            seen.add(it)
            deduped.append(it)

    if len(deduped) >= 4:
        return deduped[:4]
    if deduped:
        while len(deduped) < 4:
            deduped.append(deduped[-1])
        return deduped
    return ["블로그", "요약", "정보", "글쓰기"]


def fetch_airtable_summary_and_url(*, rowid: str) -> tuple[str, str]:
    """Airtable에서 rowid 레코드를 조회해 (summary, url)을 반환합니다."""

    _load_dotenv_if_present()
    _silence_loguru()

    try:
        from airtable_getrow import AirtableClient

        # import 과정에서 다시 sink가 설정될 수 있어 재-무력화
        _silence_loguru()
        client = AirtableClient()
        fields = client.get_record_fields(rowid)
    except Exception as e:
        raise GenerateMarkdownError(f"Airtable 조회 실패: {e}") from e

    summary = fields.get("summary")
    url = fields.get("url")

    summary_s = str(summary).strip() if summary is not None else ""
    url_s = str(url).strip() if url is not None else ""

    if not summary_s:
        raise GenerateMarkdownError("Airtable 레코드에 'summary' 필드가 없거나 비어있습니다.")
    if not url_s:
        raise GenerateMarkdownError("Airtable 레코드에 'url' 필드가 없거나 비어있습니다.")

    return summary_s, url_s


def _get_custom_api_headers() -> dict[str, str]:
    """Custom API 호출용 헤더를 구성합니다. (CUSTOM_API_KEY → X-API-Key)"""

    headers: dict[str, str] = {"Content-Type": "application/json"}
    api_key = get_custom_api_key()
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def post_chat_completions(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: float,
) -> dict[str, Any]:
    """Custom API의 OpenAI 스타일 `/v1/chat/completions`를 호출합니다."""

    url = f"{base_url}/v1/chat/completions"
    try:
        response = requests.post(
            url,
            headers=_get_custom_api_headers(),
            json={"model": model, "messages": messages},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("응답 JSON이 object(dict)가 아닙니다.")
        return data
    except requests.RequestException as e:
        raise GenerateMarkdownError(f"LLM 서버 호출 실패: {e}") from e
    except ValueError as e:
        raise GenerateMarkdownError(f"LLM 응답 파싱 실패: {e}") from e


def _llm_text_from_chat_response(resp: dict[str, Any]) -> str:
    """OpenAI 스타일 응답 JSON에서 assistant 메시지 content를 추출합니다."""

    try:
        return str(resp["choices"][0]["message"]["content"])
    except Exception as e:
        raise GenerateMarkdownError(f"LLM 응답에서 content를 추출하지 못했습니다: {e}") from e


def llm_generate_content_pack(*, summary: str, model: str) -> ContentPack:
    """summary → content/description/keywords(JSON) 생성."""

    prompt = (
        "아래 요약문을 블로그용 포스팅으로 자연스럽고 친근하게 변환해줘.\n"
        "그리고 한 줄 요약(description)과 키워드 4개도 뽑아줘.\n"
        '결과는 반드시 JSON object 하나로만 반환해줘. 키는 "content", "description", "keywords"를 사용해.\n'
        '"keywords"는 문자열 배열(list)로 4개를 넣어줘.\n\n'
        f"요약문:\n{summary}\n"
    )

    base_url = get_custom_api_base_url()
    timeout = get_custom_api_timeout()
    resp = post_chat_completions(
        base_url=base_url,
        model=model,
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout,
    )

    text = _llm_text_from_chat_response(resp)
    data = parse_json_response(text)

    content = str(data.get("content", "")).strip()
    description = _compact_ws(data.get("description", ""))
    keywords = _coerce_keywords(data.get("keywords"))

    if not content:
        raise GenerateMarkdownError("LLM이 생성한 content가 비어있습니다.")
    if not description:
        raise GenerateMarkdownError("LLM이 생성한 description이 비어있습니다.")

    return ContentPack(content=content, description=description, keywords=keywords)


def llm_generate_title(
    *,
    content: str,
    description: str,
    keywords: Iterable[str],
    model: str,
) -> str:
    """content/description/keywords 기반으로 title(JSON)을 생성합니다."""

    prompt = (
        "아래 내용을 바탕으로 블로그 글 제목(title)을 1개 만들어줘.\n"
        '결과는 반드시 JSON object 하나로만 반환해줘. 키는 "title"만 사용해.\n'
        "제목은 자연스럽고 클릭을 유도하되 과장/낚시는 피하고, 40자 이내를 권장해.\n\n"
        f"description:\n{description}\n\n"
        f"keywords:\n{', '.join(list(keywords))}\n\n"
        f"content(일부):\n{content[:1200]}\n"
    )

    try:
        base_url = get_custom_api_base_url()
        timeout = get_custom_api_timeout()
        resp = post_chat_completions(
            base_url=base_url,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
        )
        text = _llm_text_from_chat_response(resp)
        data = parse_json_response(text)
        title = _compact_ws(data.get("title", ""))
        if title:
            return title
    except Exception:
        pass

    # fallback: description을 제목처럼 정리
    fallback = description.strip()
    fallback = re.sub(r"[。\.!?]+$", "", fallback).strip()
    if len(fallback) > 45:
        fallback = fallback[:45].rstrip()
    return fallback or "새 글"


def _pick_thumbnail_url(text: str) -> str | None:
    """thumbnail_maker 출력에서 URL을 추출합니다."""

    urls = re.findall(r"https?://\S+", text)
    if not urls:
        return None

    candidates = [u.rstrip(").,]\"'") for u in urls]
    for u in reversed(candidates):
        if re.search(r"\.(png|jpg|jpeg|webp)(\?|$)", u, flags=re.IGNORECASE):
            return u
    return candidates[-1]


def generate_thumbnail(
    *,
    title: str,
    template_path: Path,
    output_path: Path,
    allow_local_fallback: bool,
) -> tuple[str, Path, str]:
    """thumbnail_maker를 실행해 (thumbnail_url, local_output_path, raw_output)을 반환합니다."""

    cmd = [
        "thumbnail_maker",
        "genthumb",
        "--title",
        title,
        "-o",
        str(output_path),
        "--template",
        str(template_path),
        "-u",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as e:
        raise GenerateMarkdownError(
            "thumbnail_maker 실행 파일을 찾을 수 없습니다. "
            "가상환경/uv 환경에서 thumbnail-maker가 설치되어 있는지 확인하세요."
        ) from e

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        raise GenerateMarkdownError(
            "thumbnail_maker 실행 실패 "
            f"(exit={proc.returncode}). 출력:\n{combined.strip()}"
        )

    url = _pick_thumbnail_url(combined)
    if url:
        return url, output_path, combined

    if allow_local_fallback:
        return output_path.as_posix(), output_path, combined

    raise GenerateMarkdownError(
        "thumbnail_maker 출력에서 URL을 찾지 못했습니다. "
        "필요하면 --allow-local-thumbnail 옵션을 사용하세요."
    )


def build_markdown(
    *,
    title: str,
    thumbnail_url: str,
    content: str,
    description: str,
    keywords: Iterable[str],
    source_url: str,
) -> str:
    """요구된 포맷으로 최종 마크다운 문자열을 구성합니다."""

    keywords_joined = ", ".join(list(keywords))
    return (
        "<!-- meta -->\n"
        f'<meta name="description" content="{_escape_html_attr(description)}">\n'
        f'<meta name="keywords" content="{_escape_html_attr(keywords_joined)}">\n'
        "<!-- /meta -->\n\n"
        f"![]({thumbnail_url})\n\n"
        f"# {title}\n\n"
        f"{content}\n\n"
        f"출처: {source_url}\n"
    )


def run_pipeline(
    *,
    rowid: str,
    model: str,
    template: str,
    allow_local_thumbnail: bool,
) -> Path:
    """
    파이프라인 전체 실행.

    성공 시 생성된 `<rowid>.md` 파일 경로를 반환합니다.
    """

    _silence_loguru()
    _load_dotenv_if_present()

    summary, source_url = fetch_airtable_summary_and_url(rowid=rowid)
    pack = llm_generate_content_pack(summary=summary, model=model)
    title = llm_generate_title(
        content=pack.content,
        description=pack.description,
        keywords=pack.keywords,
        model=model,
    )

    template_path = Path(template).expanduser().resolve()
    if not template_path.exists():
        raise GenerateMarkdownError(f"썸네일 템플릿 파일을 찾을 수 없습니다: {template_path}")

    temp_name = f"temp_{uuid4().hex}.png"
    thumb_out = Path.cwd().joinpath(temp_name).resolve()
    thumbnail_url, _thumb_path, _raw = generate_thumbnail(
        title=title,
        template_path=template_path,
        output_path=thumb_out,
        allow_local_fallback=allow_local_thumbnail,
    )

    md = build_markdown(
        title=title,
        thumbnail_url=thumbnail_url,
        content=pack.content,
        description=pack.description,
        keywords=pack.keywords,
        source_url=source_url,
    )

    out_path = Path.cwd().joinpath(f"{rowid}.md")
    out_path.write_text(md, encoding="utf-8")
    return out_path

