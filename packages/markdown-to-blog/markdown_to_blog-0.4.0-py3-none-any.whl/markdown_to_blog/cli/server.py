"""
서버 관련 명령어
"""

import os
import sys
import shutil
from pathlib import Path

import click

from . import mdb


@mdb.command("run_server", help="Django 기반 관리 서버를 실행합니다.")
@click.option("--host", default="127.0.0.1", help="호스트 주소")
@click.option("--port", default="8000", help="포트 번호")
def run_server(host: str, port: str):
    """내장된 Django 프로젝트를 이용해 관리용 웹 서버를 실행합니다."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "markdown_to_blog.server.mdb_server.settings",
    )
    from django.core.management import execute_from_command_line

    # 데이터베이스 초기화
    execute_from_command_line(["manage.py", "migrate", "--noinput"])
    execute_from_command_line(["manage.py", "runserver", f"{host}:{port}"])


@mdb.command("install_server", help="Django 서버 파일을 지정한 경로에 설치합니다.")
@click.argument("target_dir", type=click.Path())
def install_server(target_dir: str):
    """서버 프로젝트 파일을 대상 디렉터리에 복사합니다."""
    src = Path(__file__).parent.parent / "server"
    dst = Path(target_dir)
    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
        click.echo(f"서버 파일이 {dst} 에 설치되었습니다.")
    except Exception as e:
        click.echo(f"설치 실패: {e}", err=True)
        sys.exit(1)


