"""
`mdb generate_post_from_airtable` 명령어.

Airtable rowid를 입력받아 마크다운 포스트(`<rowid>.md`)를 생성합니다.
"""

from __future__ import annotations

import os

import click

from ..libs.airtable_post_generator import GenerateMarkdownError, run_pipeline
from . import mdb


@mdb.command(
    "generate_post_from_airtable", help="Airtable rowid로 마크다운 포스트를 생성합니다."
)
@click.option(
    "--row_id", "--row-id", "row_id", required=True, help="Airtable record id (rowid)"
)
@click.option(
    "--codex",
    is_flag=True,
    help="로컬 codex(exec)로 변환 작업을 수행합니다(커스텀 API 대신).",
)
@click.option(
    "--model",
    default=lambda: os.getenv("CUSTOM_API_MODEL", "codex"),
    show_default="env CUSTOM_API_MODEL 또는 codex",
    help="Custom API 모델 id",
)
@click.option(
    "--template",
    default="thumbnail_1l.thl",
    show_default=True,
    help="썸네일 템플릿 파일 경로",
)
@click.option(
    "--allow-local-thumbnail",
    is_flag=True,
    help="썸네일 URL 파싱 실패 시 로컬 파일 경로로 대체",
)
@click.option(
    "--debug",
    is_flag=True,
    help="오류 시 스택트레이스를 출력",
)
def run_generate_post_from_airtable(
    row_id: str,
    codex: bool,
    model: str,
    template: str,
    allow_local_thumbnail: bool,
    debug: bool,
) -> None:
    """
    CLI 엔트리포인트.

    - 성공 시 추가 출력 없이 `<rowid>.md` 파일만 생성합니다.
    - 실패 시에는 click 에러로 메시지를 표시합니다.
    """

    try:
        run_pipeline(
            rowid=row_id.strip(),
            model=model,
            template=template,
            allow_local_thumbnail=allow_local_thumbnail,
            use_codex=codex,
        )
    except GenerateMarkdownError as e:
        if debug:
            raise
        raise click.ClickException(str(e)) from e
