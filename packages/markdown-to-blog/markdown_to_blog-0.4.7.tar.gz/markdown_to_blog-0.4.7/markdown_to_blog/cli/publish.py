"""
발행 관련 명령어
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click
from loguru import logger

from ..libs.blogger import get_blogid, get_datetime_after, get_datetime_after_hour, upload_to_blogspot, upload_html_to_blogspot
from ..libs.markdown import read_first_header_from_md, upload_markdown_images
from ..libs.gemini import extract_keywords_and_summary
from . import mdb, add_options


@mdb.command("publish", help="마크다운 파일을 블로거에 발행합니다.")
@click.option(
    "--title",
    "-t",
    required=False,
    help="게시물 제목 (미지정 시 파일의 첫 헤더 사용)",
    default=None,
)
@click.option(
    "--draft",
    "is_draft",
    flag_value=True,
    default=False,
    help="드래프트 모드로 저장 (즉시 발행되지 않음)",
)
@click.option(
    "--after",
    "-af",
    type=click.Choice(
        ["now", "1m", "10m", "1h", "1d", "1w", "1M"], case_sensitive=True
    ),
    default=None,
    prompt=True,
    help="발행 시점 설정 (now: 즉시, 1m: 1분 후, 1h: 1시간 후, 1d: 1일 후 등)",
)
@click.option(
    "--after_hour",
    "-ah",
    type=int,
    default=None,
    help="특정 시간(시간 단위) 후 발행 (예: 3 = 3시간 후)",
)
@add_options(["blogid"])
@click.option(
    "--labels",
    "-l",
    default=None,
    help="포스트에 추가할 라벨 (여러 개 가능, 예: -l 파이썬 -l 프로그래밍)",
)
@click.option("--description", "-d", default=None, help="검색 엔진용 메타 설명 (SEO 최적화)")
@click.option("--thumbnail", help="썸네일 이미지 URL")
@click.argument("filename", type=click.Path(exists=True))
def run_publish(
    title, filename, is_draft, after, after_hour, blogid, labels, description, thumbnail
):
    """마크다운 파일을 블로거 블로그에 발행합니다.

    파일은 자동으로 HTML로 변환되어 발행되며, 이미지는 별도로 업로드되지 않습니다.
    이미지가 포함된 경우 먼저 upload_images 명령어로 이미지를 업로드하세요.
    """
    blog_id = blogid if blogid else get_blogid()

    if not title:
        title = read_first_header_from_md(filename)
        if title is None:
            logger.error(f"title is None: {filename}")
            sys.exit(1)
        title = title.replace("# ", "")
        logger.info(f"title:{title}")

    datetime_string = (
        get_datetime_after_hour(after_hour)
        if after_hour is not None
        else (
            get_datetime_after(after)
            if after is not None
            else get_datetime_after("now")
        )
    )

    # 라벨이 제공된 경우 리스트로 변환
    labels_list = None
    if labels:
        if "," in labels:
            labels_list = [label.strip() for label in labels.split(",")]
        else:
            labels_list = [labels.strip()]

    # description이 빈 문자열인 경우 None으로 변환
    if description == "":
        description = None

    try:
        post_info = upload_to_blogspot(
            title,
            filename,
            blog_id,
            is_draft=is_draft,
            datetime_string=datetime_string,
            labels=labels_list,
            search_description=description,
            thumbnail=thumbnail,
        )

        # 발행 상태 메시지
        status = "드래프트로 저장됨" if is_draft else "발행됨"
        publish_time = (
            "즉시"
            if after == "now" and after_hour is None
            else f"{after or after_hour}{'시간' if after_hour else ''} 후"
        )

        click.echo(f"게시물이 성공적으로 {status}. Post ID: {post_info['id']}, URL: {post_info['url']}")
        click.echo(f"발행 시점: {publish_time}")
        if labels_list:
            click.echo(f"라벨: {', '.join(labels_list)}")
    except Exception as e:
        click.echo(f"게시물 업로드 실패: {str(e)}", err=True)
        sys.exit(1)


@mdb.command("easy_publish", help="마크다운 파일을 Gemini로 자동 분석하여 라벨과 설명을 생성한 뒤 발행합니다.")
@click.option(
    "--title",
    "-t",
    required=False,
    help="게시물 제목 (미지정 시 파일의 첫 헤더 사용)",
    default=None,
)
@click.option(
    "--draft",
    "is_draft",
    flag_value=True,
    default=False,
    help="드래프트 모드로 저장 (즉시 발행되지 않음)",
)
@click.option(
    "--after",
    "-af",
    type=click.Choice(
        ["now", "1m", "10m", "1h", "1d", "1w", "1M"], case_sensitive=True
    ),
    default="now",
    help="발행 시점 설정 (now: 즉시, 1m: 1분 후, 1h: 1시간 후, 1d: 1일 후 등)",
)
@click.option(
    "--after_hour",
    "-ah",
    type=int,
    default=None,
    help="특정 시간(시간 단위) 후 발행 (예: 3 = 3시간 후)",
)
@add_options(["blogid"])
@click.option("--thumbnail", help="썸네일 이미지 URL")
@click.option(
    "--model",
    "-m",
    default="gemini-2.0-flash",
    help="사용할 Gemini 모델 이름 (기본값: gemini-2.0-flash)",
)
@click.argument("filename", type=click.Path(exists=True))
def run_easy_publish(
    title, filename, is_draft, after, after_hour, blogid, thumbnail, model
):
    """마크다운 파일을 Gemini로 자동 분석하여 라벨과 설명을 생성한 뒤 블로거에 발행합니다.

    이 명령어는 publish 명령어의 간소화된 버전으로, Gemini API를 사용하여
    마크다운 내용에서 자동으로 주요 키워드를 추출하여 라벨로 사용하고,
    한줄 요약을 생성하여 설명으로 사용합니다.

    주의: GEMINI_API_KEY 환경 변수가 설정되어 있어야 합니다.
    """
    blog_id = blogid if blogid else get_blogid()

    # 제목 추출
    if not title:
        title = read_first_header_from_md(filename)
        if title is None:
            logger.error(f"title is None: {filename}")
            sys.exit(1)
        title = title.replace("# ", "")
        logger.info(f"title:{title}")

    # 마크다운 파일 읽기
    try:
        with open(filename, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    except Exception as e:
        click.echo(f"마크다운 파일 읽기 실패: {str(e)}", err=True)
        sys.exit(1)

    # Gemini API를 사용하여 키워드와 요약 추출
    click.echo(f"Gemini API를 사용하여 키워드와 요약을 생성 중... (모델: {model})")
    try:
        result = extract_keywords_and_summary(markdown_content, model=model)
        keywords = result.get("keywords", [])
        description = result.get("description", "")
        
        click.echo(f"✅ 키워드 추출 완료: {', '.join(keywords) if keywords else '없음'}")
        click.echo(f"✅ 요약 생성 완료: {description if description else '없음'}")
    except Exception as e:
        click.echo(f"⚠️ Gemini API 호출 실패: {str(e)}", err=True)
        click.echo("키워드와 요약 없이 발행을 진행합니다...")
        keywords = []
        description = None

    # 발행 시점 설정
    datetime_string = (
        get_datetime_after_hour(after_hour)
        if after_hour is not None
        else (
            get_datetime_after(after)
            if after is not None
            else get_datetime_after("now")
        )
    )

    # 라벨 리스트 생성 (키워드를 라벨로 사용)
    labels_list = keywords if keywords else None

    try:
        post_info = upload_to_blogspot(
            title,
            filename,
            blog_id,
            is_draft=is_draft,
            datetime_string=datetime_string,
            labels=labels_list,
            search_description=description if description else None,
            thumbnail=thumbnail,
        )

        # 발행 상태 메시지
        status = "드래프트로 저장됨" if is_draft else "발행됨"
        publish_time = (
            "즉시"
            if after == "now" and after_hour is None
            else f"{after or after_hour}{'시간' if after_hour else ''} 후"
        )

        click.echo(f"게시물이 성공적으로 {status}. Post ID: {post_info['id']}, URL: {post_info['url']}")
        click.echo(f"발행 시점: {publish_time}")
        if labels_list:
            click.echo(f"라벨: {', '.join(labels_list)}")
        if description:
            click.echo(f"설명: {description}")
    except Exception as e:
        click.echo(f"게시물 업로드 실패: {str(e)}", err=True)
        sys.exit(1)


@mdb.command("publish_html", help="HTML 파일을 블로거에 직접 발행합니다.")
@click.argument("filename", type=click.Path(exists=True))
@click.option("--title", "-t", required=True, help="게시물 제목")
@add_options(["blogid"])
def run_publish_html(title, filename, blogid=None):
    """HTML 파일을 블로거 블로그에 직접 발행합니다.

    마크다운 변환 과정 없이 HTML 파일을 그대로 블로그에 게시합니다.
    이미 작성된 HTML 파일을 빠르게 발행할 때 유용합니다.
    """
    blog_id = blogid if blogid else get_blogid()
    try:
        post_info = upload_html_to_blogspot(title, filename, blog_id)
        click.echo(f"HTML 게시물이 성공적으로 업로드되었습니다. Post ID: {post_info['id']}, URL: {post_info['url']}")
    except Exception as e:
        click.echo(f"HTML 게시물 업로드 실패: {str(e)}", err=True)
        sys.exit(1)


@mdb.command(
    "publish_folder",
    help="폴더 내의 모든 마크다운 파일을 순차적으로 블로거에 발행합니다.",
)
@add_options(["blogid", "service", "tui"])
@click.option(
    "--interval", "-i", default=1, help="발행 간격 (시간 단위, 기본값: 1시간)"
)
@click.option(
    "--draft",
    is_flag=True,
    default=False,
    help="모든 파일을 드래프트로 저장 (즉시 발행되지 않음)",
)
@click.option(
    "--labels",
    "-l",
    multiple=True,
    help="모든 포스트에 추가할 공통 라벨",
)
@click.argument(
    "folder_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
def run_publish_folder(blogid, interval, service, tui, draft, labels, folder_path):
    """폴더 내의 모든 마크다운 파일을 순차적으로 블로거에 발행합니다.

    폴더 내 모든 마크다운(.md) 파일을 찾아 블로그에 발행합니다.
    각 파일의 이미지를 자동으로 업로드한 후 발행하며,
    지정된 시간 간격으로 순차적으로 게시됩니다.
    """
    blog_id = blogid if blogid else get_blogid()

    # 라벨이 제공된 경우 리스트로 변환
    labels_list = list(labels) if labels else None

    try:
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            click.echo(f"오류: {folder_path}는 유효한 폴더가 아닙니다.", err=True)
            sys.exit(1)

        seoul_timezone = timezone(timedelta(hours=9))
        current_dt = datetime.now(seoul_timezone)

        # 폴더 내 모든 마크다운 파일 수집
        file_list = list(folder.glob("*.md"))
        if not file_list:
            click.echo(f"경고: 폴더에 마크다운 파일이 없습니다: {folder_path}")
            return

        total_files = len(file_list)
        success_count = 0
        error_count = 0

        with click.progressbar(
            file_list, label=f"폴더 내 {total_files}개 파일 처리 중", show_pos=True
        ) as files:
            for idx, file in enumerate(files, 1):
                try:
                    # 파일 정보 준비
                    file_path = file.resolve()
                    file_name = file.name
                    file_title = read_first_header_from_md(file_path)

                    if not file_title:
                        logger.warning(
                            f"제목을 찾을 수 없음: {file_name}, 파일 이름을 제목으로 사용합니다."
                        )
                        file_title = file.stem
                    else:
                        file_title = file_title.replace("# ", "")

                    # 게시 시간 계산
                    target_dt = current_dt + timedelta(hours=interval * idx)
                    datetime_string = target_dt.isoformat(timespec="seconds")

                    # 이미지 업로드 처리
                    logger.info(f"Uploading images from file: {file_name}")
                    upload_markdown_images(str(file_path))

                    # 포스트 업로드
                    logger.info(
                        f"Publishing '{file_title}' to blog ID: {blog_id} at {datetime_string}"
                    )
                    upload_to_blogspot(
                        file_title,
                        file_path,
                        blog_id,
                        is_draft=draft,
                        datetime_string=datetime_string,
                        labels=labels_list,
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error processing file {file_name}: {str(e)}")
                    error_count += 1
                    continue

        # 완료 메시지 표시
        if success_count == total_files:
            click.echo(
                f"✅ 모든 파일이 성공적으로 처리되었습니다. (총 {total_files}개)"
            )
        else:
            click.echo(
                f"⚠️ 처리 완료: {success_count}개 성공, {error_count}개 실패 (총 {total_files}개)"
            )
    except Exception as e:
        click.echo(f"폴더 처리 중 오류 발생: {str(e)}", err=True)
        sys.exit(1)


