"""
이미지 업로드 관련 명령어
"""

import sys
import click
from typing import Optional

from ..libs.image_uploader.image_uploader import ImageUploader
from ..libs.markdown import upload_markdown_images
from . import mdb, add_options


@mdb.command("upload_image", help="이미지를 선택한 서비스에 업로드합니다.")
@click.argument("image_path", type=click.Path(exists=True))
@add_options(["service"])
def run_upload_image(image_path: str, service: Optional[str] = None):
    """지정된 이미지 파일을 이미지 호스팅 서비스에 업로드합니다.

    업로드 성공 시 이미지 URL을 반환합니다.
    서비스를 지정하지 않으면 설정된 기본값 또는 랜덤으로 선택됩니다.
    """
    try:
        uploader = ImageUploader(service=service)
        url = uploader.upload(image_path)
        click.echo(f"업로드 성공: {url}")
    except Exception as e:
        click.echo(f"업로드 실패: {str(e)}", err=True)
        sys.exit(1)


@mdb.command("upload_images", help="마크다운 파일 내의 모든 이미지를 업로드합니다.")
@click.option(
    "--input",
    "-i",
    "input_",
    required=True,
    help="업로드할 이미지가 포함된 마크다운 파일 경로",
)
def run_upload_images(input_):
    """마크다운 파일 내 모든 이미지를 찾아 업로드하고 링크를 업데이트합니다.

    파일 내에서 이미지 링크를 찾아 자동으로 업로드한 뒤 원본 파일의 링크를
    업로드된 URL로 교체합니다.
    """
    upload_markdown_images(input_)
    click.echo("이미지 업로드 완료")
    sys.exit(1)


