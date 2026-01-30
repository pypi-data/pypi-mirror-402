"""
GUI 관련 명령어
"""

import sys
import asyncio
import click

from . import mdb


@mdb.command("gui", help="GUI 모드로 실행합니다.")
def run_gui():
    """PySide6 기반 GUI를 실행합니다."""
    try:
        from ..gui import run_gui as start_gui
        start_gui()
    except ImportError as e:
        click.echo(f"GUI 실행에 필요한 패키지가 설치되지 않았습니다: {e}", err=True)
        click.echo("다음 명령어로 필요한 패키지를 설치하세요:")
        click.echo("uv sync")
        sys.exit(1)
    except Exception as e:
        click.echo(f"GUI 실행 중 오류 발생: {e}", err=True)
        sys.exit(1)


@mdb.command("gui-shell", help="GUI Shell 모드로 실행합니다 (Tortoise ORM).")
@click.argument("shell_command", required=False, default=None)
def run_gui_shell(shell_command):
    """Tortoise ORM 기반 인터랙티브 Shell을 실행합니다."""
    try:
        from ..gui import run_shell
        asyncio.run(run_shell(shell_command))
    except ImportError as e:
        click.echo(f"Shell 실행에 필요한 패키지가 설치되지 않았습니다: {e}", err=True)
        click.echo("다음 명령어로 필요한 패키지를 설치하세요:")
        click.echo("uv sync")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Shell 실행 중 오류 발생: {e}", err=True)
        sys.exit(1)

