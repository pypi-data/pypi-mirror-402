"""
인증 관련 명령어
"""

import sys
import click

from ..libs.blogger import check_config, get_blogger_service, set_client_secret
from . import mdb


@mdb.command(
    "set_client_secret", help="Google API 클라이언트 시크릿 파일을 설정합니다."
)
@click.argument("filename", type=click.Path(exists=True))
def run_set_client_secret(filename):
    """Google API 인증을 위한 client_secret.json 파일을 설정합니다.

    블로거 API를 사용하려면 Google Cloud Console에서 발급받은
    클라이언트 시크릿 파일이 필요합니다.
    """
    try:
        set_client_secret(filename)
        click.echo(f"클라이언트 시크릿 파일이 성공적으로 설정되었습니다: {filename}")
    except Exception as e:
        click.echo(f"클라이언트 시크릿 설정 실패: {str(e)}", err=True)
        sys.exit(1)


@mdb.command("refresh_auth", help="Google API 인증 정보를 갱신합니다.")
def run_refresh_auth():
    """Google API 인증 정보를 갱신합니다.

    인증 토큰이 만료되었거나 오류가 발생하는 경우 이 명령어를 사용하여
    인증 정보를 갱신할 수 있습니다.
    """
    try:
        sys.argv[1] = "--noauth_local_webserver"
        get_blogger_service()
        click.echo("인증 정보가 성공적으로 갱신되었습니다.")
    except Exception as e:
        click.echo(f"인증 정보 갱신 실패: {str(e)}", err=True)
        sys.exit(1)


