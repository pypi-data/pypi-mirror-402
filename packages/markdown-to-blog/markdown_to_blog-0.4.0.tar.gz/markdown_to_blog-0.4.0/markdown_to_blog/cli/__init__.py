"""
CLI 명령어 모듈 - 메인 command group과 공통 유틸리티
"""

import click
from typing import List, Callable

from ..libs.click_order import CustomOrderGroup
from ..libs.image_uploader.services import get_available_services

# 공통 옵션 기본값 및 설명
COMMON_OPTIONS = {
    "tui": {
        "is_flag": True,
        "default": False,
        "help": "TUI(Text User Interface) 모드로 진행 상황을 표시합니다.",
    },
    "blogid": {
        "param": "--blogid",
        "short": "-b",
        "default": None,
        "help": "업로드하려는 블로그 ID 지정. 미지정 시 설정값 사용.",
    },
    "service": {
        "param": "--service",
        "short": "-s",
        "type": click.Choice(get_available_services(), case_sensitive=False),
        "help": "사용할 이미지 업로드 서비스. 미지정 시 랜덤 선택.",
    },
}


def add_options(options: List[str]) -> Callable:
    """옵션들을 명령어에 일관되게 추가하는 데코레이터 함수"""

    def decorator(f):
        for option_name in reversed(options):
            if option_name == "tui":
                f = click.option("--tui", **COMMON_OPTIONS["tui"])(f)
            elif option_name == "blogid":
                f = click.option(
                    COMMON_OPTIONS["blogid"]["param"],
                    COMMON_OPTIONS["blogid"]["short"],
                    default=COMMON_OPTIONS["blogid"]["default"],
                    help=COMMON_OPTIONS["blogid"]["help"],
                )(f)
            elif option_name == "service":
                f = click.option(
                    COMMON_OPTIONS["service"]["param"],
                    COMMON_OPTIONS["service"]["short"],
                    type=COMMON_OPTIONS["service"]["type"],
                    help=COMMON_OPTIONS["service"]["help"],
                )(f)
        return f

    return decorator


@click.command(
    cls=CustomOrderGroup,
    order=[
        "set_blogid",
        "get_blogid",
        "generate_post_from_airtable",
        "convert",
        "refresh_auth",
        "set_client_secret",
        "backup-posting",
        "sync-posting",
        "update-posting",
        "delete-posting",
        "save-as-markdown",
        "publish",
        "easy_publish",
        "upload_image",
        "upload_images",
        "publish_folder",
        "publish_html",
        "list_my_blogs",
        "gui",
        "run_server",
        "install_server",
        "daemon",
    ],
)
def mdb():
    """Markdown to Blogger - 마크다운 파일을 블로거에 발행하는 도구."""
    click.echo("markdown to blogger\nresult:\n\n")


# 명령어 모듈들을 import하여 명령어 등록
from . import (
    blog,
    auth,
    convert,
    publish,
    posting,
    image,
    gui,
    server,
    daemon,
    generate_post_from_airtable,
)

__all__ = ["mdb", "add_options", "COMMON_OPTIONS"]

