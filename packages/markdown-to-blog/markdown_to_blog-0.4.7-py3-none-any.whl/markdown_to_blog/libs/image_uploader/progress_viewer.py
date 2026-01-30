from typing import List
from datetime import datetime


class ImageUploadStatus:
    """이미지 업로드 상태를 추적하는 클래스"""

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.status = "대기"  # 대기, 진행중, 완료, 실패
        self.current_service = ""
        self.attempt = 0
        self.progress = 0
        self.url = ""
        self.error = ""


class ProgressViewer:
    """진행 상황 뷰어 인터페이스"""

    def __init__(
        self, markdown_file: str, image_files: List[str], use_tui: bool = True
    ):
        self.markdown_file = markdown_file
        self.image_statuses = {img: ImageUploadStatus(img) for img in image_files}
        self.total_files = len(image_files)
        self.completed_files = 0
        self._last_update = datetime.now()
        self._update_interval = 0.5  # 업데이트 간격 (초)

        # 초기 상태 출력
        print(f"\n마크다운 파일: {markdown_file}")
        print(f"총 이미지 파일: {self.total_files}개\n")
        self._print_progress_bar()

    def start(self):
        """진행 상황 표시 시작"""
        pass

    def update(
        self,
        image_path: str,
        status: str,
        service: str = "",
        attempt: int = 0,
        progress: int = 0,
        url: str = "",
        error: str = "",
    ) -> None:
        """진행 상황 업데이트"""
        if image_path not in self.image_statuses:
            return

        status_obj = self.image_statuses[image_path]
        status_obj.status = status
        status_obj.current_service = service
        status_obj.attempt = attempt
        status_obj.progress = progress
        status_obj.url = url
        status_obj.error = error

        # 완료된 파일 수 업데이트
        self.completed_files = sum(
            1 for s in self.image_statuses.values() if s.status in ["완료", "실패"]
        )

        # 현재 상태 출력
        self._print_status(image_path)

    def stop(self):
        """진행 상황 표시 종료"""
        print("\n업로드 완료!")
        print(
            f"성공: {sum(1 for s in self.image_statuses.values() if s.status == '완료')}개"
        )
        print(
            f"실패: {sum(1 for s in self.image_statuses.values() if s.status == '실패')}개\n"
        )

    def _print_progress_bar(self):
        """전체 진행 상황 막대 출력"""
        progress = (self.completed_files / self.total_files) * 100
        bar_width = 50
        filled = int(bar_width * self.completed_files / self.total_files)
        bar = "=" * filled + "-" * (bar_width - filled)
        print(
            f"\r진행률: [{bar}] {progress:.1f}% ({self.completed_files}/{self.total_files})",
            end="",
            flush=True,
        )

    def _print_status(self, image_path: str):
        """현재 파일의 상태 출력"""
        status = self.image_statuses[image_path]

        # 진행 상황 막대 업데이트
        self._print_progress_bar()

        # 현재 파일 상태 출력
        if status.status == "진행중":
            print(f"\n현재 파일: {image_path}")
            print(f"서비스: {status.current_service} (시도 {status.attempt})")
            if status.error:
                print(f"오류: {status.error}")
        elif status.status == "완료":
            print(f"\n완료: {image_path} -> {status.url}")
        elif status.status == "실패":
            print(f"\n실패: {image_path} ({status.error})")
