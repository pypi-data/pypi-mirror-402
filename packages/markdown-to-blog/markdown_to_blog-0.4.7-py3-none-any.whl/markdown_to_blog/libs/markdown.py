import codecs
import os
import pprint
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

from loguru import logger
from markdown2 import Markdown

from .image_uploader.file_handler import FileHandler
from .image_uploader.image_downloader import ImageDownloader
from .image_uploader.image_uploader import ImageUploader
from .image_uploader.image_upload_service import DefaultImageUploader
from .image_uploader.exceptions import ImageUploadError
from .image_uploader.config import UploadConfig
from .image_uploader.url_handler import URLHandler
from .md_converter.base import MarkdownConverter

DEFAULT_MARKDOWN_EXTRAS = [
    "highlightjs-lang",
    "fenced-code-blocks",
    "footnotes",
    "tables",
    "code-friendly",
    "smarty-pants",
    "metadata",
]


def convert_markdown(converter: MarkdownConverter, text: str):
    return converter.convert(text)


def convert(input_fn, output_fn, is_temp=False):
    with codecs.open(input_fn, "r", "utf_8") as fp:
        markdowner = Markdown(extras=DEFAULT_MARKDOWN_EXTRAS)
        html = markdowner.convert(fp.read())
        with codecs.open(output_fn, "w", "utf_8") as fwp:
            fwp.write(html)


def read_first_header_from_md(file_path) -> Optional[str]:
    """
    마크다운 파일로부터 첫 번째 헤더를 읽어 반환하는 함수.
    :param file_path: 마크다운 파일의 경로
    :return: 첫 번째 헤더 (문자열), 헤더가 없으면 None 반환
    """
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # 마크다운 헤더는 '#'으로 시작함
            if line.startswith("#"):
                return line.strip()  # 헤더 반환 전 앞뒤 공백 제거
    return None  # 파일에 헤더가 없는 경우


def _extract_images_from_markdown(file_path: str) -> List[Tuple[int, str]]:
    """마크다운 파일에서 이미지 링크를 추출하는 함수

    Args:
        file_path (str): 마크다운 파일 경로

    Returns:
        List[Tuple[int, str]]: (라인 번호, 이미지 링크) 튜플의 리스트

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        IOError: 파일 읽기 오류 발생 시
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    images = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file.readlines()):
                if line.startswith("![") and "]" in line:
                    try:
                        image_link = line.split("(")[1].split(")")[0].strip()
                        if image_link:  # 빈 링크 제외
                            images.append((i, image_link))
                    except IndexError:
                        logger.warning(
                            f"잘못된 이미지 링크 형식 (라인 {i + 1}): {line.strip()}"
                        )
    except IOError as e:
        logger.error(f"Error reading markdown file: {e}")
        raise

    return images


def _prepare_image(image_link: str, config: UploadConfig) -> str:
    """이미지 링크를 처리하여 업로드 가능한 형태로 준비하는 함수

    Args:
        image_link (str): 이미지 링크 (URL 또는 파일 경로)
        config (UploadConfig): 업로드 설정

    Returns:
        str: 업로드할 이미지의 경로

    Raises:
        ImageUploadError: 이미지 준비 실패 시
    """
    # URL인 경우 다운로드
    if image_link.lower().startswith(("http://", "https://")):
        try:
            url_handler = URLHandler()
            file_handler = FileHandler()
            downloader = ImageDownloader(config)

            encoded_url = url_handler.encode_url(image_link)
            extension = url_handler.get_file_extension(image_link)
            temp_path = file_handler.create_temp_file(extension)

            try:
                downloader.download(encoded_url, temp_path)
                return temp_path
            except Exception as e:
                file_handler.cleanup_temp_file(temp_path)
                raise ImageUploadError(f"이미지 다운로드 실패: {str(e)}")
        except Exception as e:
            raise ImageUploadError(f"URL 처리 실패: {str(e)}")

    # 로컬 파일인 경우 경로 검증
    try:
        file_handler = FileHandler()
        return file_handler.validate_file_exists(image_link)
    except Exception as e:
        raise ImageUploadError(f"파일 검증 실패: {str(e)}")


def _upload_image_with_retry(
    image_link: str,
    services: List[str],
    config: UploadConfig,
    max_retries: int = 3,
    use_tui: bool = False,
) -> Tuple[str, str]:
    """
    이미지를 업로드하고 실패 시 다른 서비스로 재시도하는 함수

    Args:
        image_link (str): 업로드할 이미지의 경로 또는 URL
        services (List[str]): 사용 가능한 업로드 서비스 목록
        config (UploadConfig): 업로드 설정
        max_retries (int): 최대 재시도 횟수
        use_tui (bool): TUI 모드 사용 여부

    Returns:
        Tuple[str, str]: (원본 이미지 링크, 업로드된 URL)

    Raises:
        ImageUploadError: 모든 서비스로 업로드 실패 시
    """
    if not services:
        raise ValueError("No available upload services")

    # 이미지 다운로드 또는 로컬 파일 경로 확인
    try:
        image_path = _prepare_image(image_link, config)
    except Exception as e:
        logger.error(f"Error preparing image {image_link}: {e}")
        raise ImageUploadError(f"Failed to prepare image: {e}")

    # 각 서비스로 업로드 시도
    used_services = set()
    last_error = None

    for _ in range(max_retries):
        # 사용하지 않은 서비스 선택
        available_services = [s for s in services if s not in used_services]
        if not available_services:
            used_services.clear()
            available_services = services

        service = random.choice(available_services)
        used_services.add(service)

        try:
            uploader = DefaultImageUploader(service=service, use_tui=use_tui)
            uploaded_url = uploader.upload(image_path)

            if uploaded_url:
                logger.info(f"Successfully uploaded image to {service}: {uploaded_url}")
                return image_link, uploaded_url

        except Exception as e:
            last_error = e
            logger.warning(f"Upload failed with {service}: {e}")
            continue

    error_msg = f"Failed to upload image after {max_retries} attempts with services: {', '.join(used_services)}"
    if last_error:
        error_msg += f"\nLast error: {str(last_error)}"
    raise ImageUploadError(error_msg)


def upload_markdown_images(
    file_path: str,
) -> None:
    """마크다운 파일의 이미지들을 업로드하고 원본 파일을 수정하는 함수

    Args:
        file_path (str): 마크다운 파일 경로

    Returns:
        Dict[str, str]: {원본 이미지 링크: 업로드된 이미지 URL} 형태의 매핑

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        IOError: 파일 읽기/쓰기 오류 발생 시
    """
    logger.info(f"마크다운 파일 이미지 업로드 시작: {file_path}")

    # 이미지 추출
    image_links = _extract_images_from_markdown(file_path)
    if not image_links:
        logger.info(f"마크다운 파일에 이미지가 없습니다: {file_path}")
        return {}

    total_images = len(image_links)
    logger.info(f"발견된 이미지 개수: {total_images}")
    logger.info(f"{pprint.pformat(image_links)}")
    logger.info("===================================== trye")

    # 설정 및 업로더 준비
    # config = UploadConfig()
    # uploader = ImageUploader(config=config, service=service, use_tui=use_tui)
    image_links = [link for _, link in image_links]
    # 통합 업로더 경로 사용: 순차 업로드로 매핑 생성
    config = UploadConfig()
    unified_uploader = ImageUploader(config=config)
    image_map: Dict[str, str] = {}
    for link in image_links:
        try:
            prepared = _prepare_image(link, config)
            new_url = unified_uploader.upload(prepared)
            image_map[link] = new_url
            # URL 원본의 경우 임시 파일 정리
            if link.lower().startswith(("http://", "https://")) and os.path.exists(prepared):
                try:
                    os.remove(prepared)
                except OSError:
                    pass
        except Exception as e:
            logger.error(f"이미지 업로드 실패: {link} -> {e}")
    logger.info(f"image_map: {pprint.pformat(image_map)}")
    # 파일 콘텐츠 읽기
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    logger.info(f"- content: {pprint.pformat(content)}")
    # 업로드 성공한 이미지가 있으면 파일 수정
    if image_map:
        # 링크 교체
        updated_content = _replace_image_links(content, image_map)

        logger.info("-- updated_content --")
        logger.info(f"{pprint.pformat(updated_content)}")
        # 파일에 쓰기
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(updated_content)

        success_count = len(image_map)
        if success_count < total_images:
            logger.warning(f"이미지 업로드 결과: {success_count}/{total_images} 성공")
        else:
            logger.info(f"모든 이미지 업로드 완료: {success_count}/{total_images}")
    else:
        logger.warning("업로드된 이미지가 없습니다. 파일을 수정하지 않습니다.")

    return None


def _process_images_sequential(
    image_links: List[Tuple[int, str]],
    uploader: ImageUploader,
    config: UploadConfig,
    max_retries: int = 3,
) -> Dict[str, str]:
    """이미지를 순차적으로 처리하는 함수

    Args:
        image_links: 업로드할 이미지 목록 (라인 번호, 이미지 링크) 튜플 리스트
        uploader: 이미지 업로더 인스턴스
        config: 업로드 설정
        max_retries: 실패 시 최대 재시도 횟수

    Returns:
        Dict[str, str]: {원본 이미지 링크: 업로드된 이미지 URL} 형태의 매핑
    """
    image_map = {}
    total_images = len(image_links)

    for idx, (line_num, image_link) in enumerate(image_links, 1):
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            try:
                if retry_count > 0:
                    logger.info(
                        f"이미지 업로드 재시도 ({retry_count}/{max_retries}): {image_link}"
                    )

                # 이미지 준비 (URL이면 다운로드, 로컬이면 경로 검증)
                prepared_image = _prepare_image(image_link, config)

                # 이미지 업로드
                new_url = uploader.upload(prepared_image)

                # 원본 이미지가 URL인 경우 임시 파일 삭제
                if image_link.lower().startswith(
                    ("http://", "https://")
                ) and os.path.exists(prepared_image):
                    try:
                        os.remove(prepared_image)
                    except OSError:
                        logger.warning(f"임시 파일 삭제 실패: {prepared_image}")

                # 결과 저장
                image_map[image_link] = new_url
                logger.info(f"이미지 업로드 성공 ({idx}/{total_images}): {new_url}")

                success = True

                # API 호출 제한 방지를 위한 짧은 딜레이
                time.sleep(0.5)

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"이미지 업로드 실패 (라인 {line_num + 1}): {str(e)}")
                    logger.debug(f"실패한 이미지 링크: {image_link}")
                time.sleep(1)  # 재시도 간 대기

    return image_map


def _process_images_parallel(
    image_links: List[Tuple[int, str]],
    uploader: ImageUploader,
    config: UploadConfig,
    max_workers: int = 4,
    max_retries: int = 3,
) -> Dict[str, str]:
    """이미지를 병렬로 처리하는 함수

    Args:
        image_links: 업로드할 이미지 목록 (라인 번호, 이미지 링크) 튜플 리스트
        uploader: 이미지 업로더 인스턴스
        config: 업로드 설정
        max_workers: 최대 병렬 처리 작업자 수
        max_retries: 실패 시 최대 재시도 횟수

    Returns:
        Dict[str, str]: {원본 이미지 링크: 업로드된 이미지 URL} 형태의 매핑
    """
    results = {}

    def upload_single_image(
        image_data: Tuple[int, str],
    ) -> Tuple[int, str, Optional[str], Optional[str]]:
        """개별 이미지 업로드 처리 함수

        Returns:
            Tuple[int, str, Optional[str], Optional[str]]:
                (라인 번호, 원본 링크, 업로드된 URL 또는 None, 에러 메시지 또는 None)
        """
        line_num, image_link = image_data
        retry_count = 0

        while retry_count < max_retries:
            try:
                prepared_image = _prepare_image(image_link, config)
                new_url = uploader.upload(prepared_image)

                # 원본 이미지가 URL인 경우 임시 파일 삭제
                if image_link.lower().startswith(
                    ("http://", "https://")
                ) and os.path.exists(prepared_image):
                    try:
                        os.remove(prepared_image)
                    except OSError:
                        pass  # 임시 파일 삭제 실패는 무시

                return line_num, image_link, new_url, None  # 성공
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return line_num, image_link, None, str(e)  # 최종 실패
                time.sleep(1)  # 재시도 간 대기

        # 이 지점에 도달하면 모든 재시도가 실패한 경우임
        return line_num, image_link, None, "Maximum retries exceeded"

    # 병렬 처리 실행
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(upload_single_image, img): img for img in image_links
        }

        for future in as_completed(futures):
            line_num, original_link, new_url, error = future.result()
            if error:
                logger.error(f"이미지 업로드 실패 (라인 {line_num + 1}): {error}")
                logger.debug(f"실패한 이미지 링크: {original_link}")
            else:
                results[original_link] = new_url
                logger.info(f"이미지 업로드 성공 (라인 {line_num + 1}): {new_url}")

    return results


def _replace_image_links(
    content: str,
    image_map: Dict[str, str],
) -> str:
    """마크다운 파일 내용의 이미지 링크를 새 URL로 교체

    Args:
        content: 파일 내용 (라인 리스트)
        image_positions: 이미지 위치 정보 (라인 번호, 원본 링크) 튜플 리스트
        image_map: 이미지 교체 매핑 {원본 링크: 새 URL}

    Returns:
        List[str]: 업데이트된 파일 내용
    """
    logger.info("이미지 링크 교체 시작")
    logger.debug(f"교체할 이미지 매핑: {image_map}")

    updated_content = content

    for original_link, new_link in image_map.items():
        logger.info(f"new_link: {new_link}, original_link: {original_link}")
        logger.info(f"original_link: {original_link} in image_map")
        if original_link in updated_content:
            updated_content = updated_content.replace(
                f"({original_link})", f"({new_link})"
            )
        # new_url = image_map[original_link]
        # line = content[line_num] # type: ignore
        # updated_line = line.replace(f"({original_link})", f"({new_url})")
        # updated_content[line_num] = updated_line # type: ignore
        # logger.debug(f"라인 {line_num}: {original_link} -> {new_url}")

    logger.info("이미지 링크 교체 완료")
    return updated_content
