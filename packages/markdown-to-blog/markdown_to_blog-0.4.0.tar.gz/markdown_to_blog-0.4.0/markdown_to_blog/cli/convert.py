"""
변환 관련 명령어
"""

import sys
import click
from pathlib import Path
from typing import Optional

from ..libs.markdown import convert
from ..libs.web_to_markdown import fetch_html_with_playwright, convert_html_to_markdown, HTMLFetchError
from . import mdb


@mdb.command("convert", help="마크다운 파일을 HTML로 변환합니다.")
@click.option(
    "--input", "-i", "input_", required=True, help="변환할 마크다운 파일 경로"
)
@click.option("--output", "-o", "output_", required=True, help="저장할 HTML 파일 경로")
def run_convert(input_, output_):
    """마크다운 파일을 HTML 파일로 변환합니다.

    코드 하이라이팅, 표, 이미지 등을 포함한 마크다운을 HTML로 변환합니다.
    변환된 HTML은 지정된 출력 파일에 저장됩니다.
    """
    try:
        convert(input_, output_)
        click.echo(f"변환 완료: {input_} -> {output_}")
    except Exception as e:
        click.echo(f"변환 실패: {str(e)}", err=True)
        sys.exit(1)


@mdb.command("save-as-markdown", help="Fetches a URL, converts its content to Markdown, and saves it.")
@click.option("--url", "url_option", required=True, help="The URL of the web page to fetch and convert.")
@click.option("--output", "output_filepath_option", required=True, type=click.Path(dir_okay=False, resolve_path=True, writable=True), help="Path to save the resulting Markdown file.")
@click.option("--start-comment", "start_comment_option", default=None, type=str, help="Text content of the HTML start comment for extraction (e.g., '본문').")
@click.option("--end-comment", "end_comment_option", default=None, type=str, help="Text content of the HTML end comment for extraction (e.g., '//본문').")
def run_save_as_markdown(
    url_option: str, 
    output_filepath_option: str,
    start_comment_option: Optional[str],
    end_comment_option: Optional[str]
):
    """
    Fetches a web page, converts its HTML content to Markdown, and saves it to a file.
    """
    click.echo(f"Fetching content from {url_option}...")
    try:
        html_content = fetch_html_with_playwright(
            url_option,
            start_comment=start_comment_option,
            end_comment=end_comment_option
        )
        if not html_content:
            click.echo(f"Warning: No content fetched from '{url_option}'. This might be due to missing comments, an empty page section, or an issue with the page.", err=True)
    except HTMLFetchError as e:
        click.echo(f"Error fetching URL '{url_option}': {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred during fetching: {e}", err=True)
        sys.exit(1)

    click.echo("Converting HTML to Markdown...")
    try:
        markdown_content = convert_html_to_markdown(html_content)
    except Exception as e:
        click.echo(f"Error converting HTML to Markdown: {e}", err=True)
        sys.exit(1)

    try:
        output_path = Path(output_filepath_option)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding='utf-8')
        click.echo(f"Successfully saved Markdown from '{url_option}' to '{output_path}'")
    except IOError as e:
        click.echo(f"Error writing to output file '{output_filepath_option}': {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred while writing file: {e}", err=True)
        sys.exit(1)

