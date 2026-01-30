"""
블로그 설정 관련 명령어
"""

import click
from loguru import logger

from ..libs.blogger import check_config, get_blogid, set_blogid, list_my_blogs
from . import mdb, add_options


@mdb.command("set_blogid", help="블로그 ID를 설정합니다.")
@click.argument("blogid")
def run_set_blogid(blogid):
    """블로거 블로그 ID를 설정합니다.

    설정된 블로그 ID는 다른 명령어에서 기본값으로 사용됩니다.
    블로그 ID는 블로거 관리 페이지 또는 URL에서 확인할 수 있습니다.
    """
    check_config()
    set_blogid(blogid)
    click.echo(f"블로그 ID가 성공적으로 설정되었습니다: {blogid}")


@mdb.command("get_blogid", help="현재 설정된 블로그 ID를 확인합니다.")
def run_get_blogid():
    """현재 설정된 블로그 ID를 출력합니다."""
    check_config()
    blog_id = get_blogid()
    click.echo(f"현재 설정된 블로그 ID: {blog_id}")


@mdb.command("list_my_blogs", help="현재 계정에서 소유한 블로그들의 id와 url(도메인)을 출력합니다.")
def run_list_my_blogs():
    """현재 계정에서 소유한 블로그들의 id와 url(도메인)을 출력합니다."""
    list_my_blogs()

