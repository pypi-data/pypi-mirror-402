"""
Daemon 서버 관련 명령어
"""

import sys
import os
import json
import subprocess
import time
from typing import Optional

import click
from loguru import logger

from ..libs.daemon_client import create_client
from ..libs.daemon_server import run_daemon_server
from . import mdb


@mdb.group("daemon", help="Daemon 서버를 시작/중지/상태 확인합니다.")
def daemon():
    """Daemon 서버를 관리합니다."""
    pass


@daemon.command("start", help="Daemon 서버를 시작합니다.")
@click.option(
    "--bind",
    "-b",
    default="tcp://127.0.0.1:5555",
    help="서버 바인드 주소 (기본값: tcp://127.0.0.1:5555)",
)
@click.option(
    "--foreground",
    "-f",
    is_flag=True,
    default=False,
    help="백그라운드가 아닌 포그라운드에서 실행 (기본값: 백그라운드)",
)
def daemon_start(bind: str, foreground: bool):
    """Daemon 서버를 시작합니다."""
    try:
        if foreground:
            # 포그라운드 모드
            run_daemon_server(bind)
        else:
            # 백그라운드 모드
            import platform
            from pathlib import Path
            
            # 로그 파일 경로 설정
            log_dir = Path.home() / ".markdown_to_blog"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "daemon.log"
            
            # 프로젝트 루트 경로 찾기
            current_dir = os.getcwd()
            
            # Python 스크립트를 백그라운드에서 실행
            script = f"""
import sys
import os
sys.path.insert(0, r'{current_dir}')
from markdown_to_blog.libs.daemon_server import run_daemon_server
run_daemon_server(r'{bind}')
"""
            
            if platform.system() == "Windows":
                # Windows에서는 로그 파일로 리다이렉트
                with open(log_file, "a") as log:
                    process = subprocess.Popen(
                        [sys.executable, "-c", script],
                        stdout=log,
                        stderr=log,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
            else:
                # Unix 계열에서는 nohup과 비슷하게
                with open(log_file, "a") as log:
                    process = subprocess.Popen(
                        [sys.executable, "-c", script],
                        stdout=log,
                        stderr=log,
                        start_new_session=True
                    )
            
            # 프로세스가 제대로 시작되었는지 확인
            time.sleep(0.5)
            
            if process.poll() is None:
                click.echo(f"✅ Daemon 서버가 백그라운드에서 시작되었습니다: {bind}")
                click.echo(f"📝 로그 파일: {log_file}")
                click.echo(f"🆔 프로세스 ID: {process.pid}")
            else:
                # 프로세스가 즉시 종료된 경우
                click.echo(f"❌ Daemon 서버 시작 실패. 로그를 확인하세요: {log_file}", err=True)
                if log_file.exists():
                    with open(log_file, "r") as f:
                        last_lines = f.readlines()[-10:]
                        click.echo("\n마지막 로그:")
                        click.echo("".join(last_lines))
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"Daemon 시작 실패: {str(e)}", err=True)
        logger.exception("Daemon 시작 중 예외 발생")
        sys.exit(1)


@daemon.command("stop", help="Daemon 서버를 중지합니다.")
@click.option(
    "--address",
    "-a",
    default="tcp://127.0.0.1:5555",
    help="서버 주소 (기본값: tcp://127.0.0.1:5555)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="강제 종료 (프로세스 직접 종료)",
)
def daemon_stop(address: str, force: bool):
    """Daemon 서버를 중지합니다."""
    try:
        if force:
            # 강제 종료: 프로세스 직접 종료
            import psutil
            import platform
            
            # 5555 포트를 사용하는 프로세스 찾기
            port = int(address.split(":")[-1]) if ":" in address else 5555
            found = False
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'daemon_server' in cmdline or 'run_daemon_server' in cmdline:
                            proc.kill()
                            click.echo(f"✅ 프로세스 {proc.info['pid']}를 종료했습니다.")
                            found = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if not found:
                click.echo("⚠️ 실행 중인 Daemon 프로세스를 찾을 수 없습니다.")
        else:
            # 정상 종료: shutdown 명령 전송
            client = create_client(address, timeout=5)
            response = client.send_command("shutdown")
            
            if response.get("status") == "success":
                click.echo("✅ Daemon 서버가 중지되었습니다.")
            else:
                click.echo(f"⚠️ {response.get('error', 'Unknown error')}")
    except (TimeoutError, ConnectionError) as e:
        click.echo(f"⚠️ 서버에 연결할 수 없습니다: {str(e)}")
        click.echo("💡 --force 옵션을 사용하여 강제 종료할 수 있습니다.")
    except ImportError:
        click.echo("❌ 강제 종료를 위해서는 psutil이 필요합니다: pip install psutil")
    except Exception as e:
        click.echo(f"❌ Daemon 서버 중지 실패: {str(e)}", err=True)


@daemon.command("status", help="Daemon 서버 상태를 확인합니다.")
@click.option(
    "--address",
    "-a",
    default="tcp://127.0.0.1:5555",
    help="서버 주소 (기본값: tcp://127.0.0.1:5555)",
)
def daemon_status(address: str):
    """Daemon 서버 상태를 확인합니다."""
    try:
        client = create_client(address, timeout=5)
        response = client.send_command("ping")
        
        if response.get("status") == "success":
            click.echo("✅ Daemon 서버가 정상적으로 실행 중입니다.")
            data = response.get("data", {})
            if data:
                click.echo(f"   서버 주소: {address}")
                if "uptime" in data:
                    click.echo(f"   업타임: {data['uptime']}")
        else:
            click.echo("❌ Daemon 서버가 응답하지 않습니다.", err=True)
    except Exception as e:
        click.echo("❌ Daemon 서버에 연결할 수 없습니다.", err=True)
        click.echo(f"   오류: {str(e)}")


@daemon.command("execute", help="Daemon 서버에서 명령어를 실행합니다.")
@click.argument("command")
@click.option("--params", "-p", help="JSON 형태의 파라미터")
@click.option(
    "--address",
    "-a",
    default="tcp://127.0.0.1:5555",
    help="서버 주소 (기본값: tcp://127.0.0.1:5555)",
)
def daemon_execute(command: str, params: Optional[str], address: str):
    """Daemon 서버에서 명령어를 실행합니다."""
    try:
        # 파라미터 파싱
        parsed_params = {}
        if params:
            parsed_params = json.loads(params)
        
        client = create_client(address)
        response = client.send_command(command, parsed_params)
        
        if response.get("status") == "success":
            data = response.get("data", {})
            if isinstance(data, dict):
                click.echo(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                click.echo(data)
        else:
            error = response.get("error", "Unknown error")
            click.echo(f"실행 실패: {error}", err=True)
            sys.exit(1)
            
    except json.JSONDecodeError:
        click.echo("파라미터는 유효한 JSON이어야 합니다.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"명령어 실행 실패: {str(e)}", err=True)
        sys.exit(1)


