from typing import List, Optional


def get_available_services() -> List[str]:
    """사용 가능한 이미지 업로드 서비스 목록을 반환

    Returns:
        List[str]: 사용 가능한 이미지 업로드 서비스의 목록
    """
    return "anhmoe beeimg fastpic imagebin pixhost sxcu".split() # type: ignore


def upload_image(file_path: str, service: Optional[str] = None) -> str:
    """
    편의 함수: 이미지 업로드

    Args:
        file_path (str): 업로드할 이미지 파일 경로
        service (Optional[str]): 사용할 특정 업로드 서비스

    Returns:
        str: 업로드된 이미지의 URL

    Raises:
        ValueError: 지원하지 않는 서비스가 지정된 경우
        ImageUploadError: 업로드 실패 시
    """
    if service and service not in get_available_services():
        raise ValueError(
            f"지원하지 않는 서비스입니다. 사용 가능한 서비스: {', '.join(get_available_services())}"
        )

    # 순환 참조를 피하기 위해 여기서 import
    from .image_uploader import ImageUploader

    uploader = ImageUploader(service=service)
    return uploader.upload(file_path)
