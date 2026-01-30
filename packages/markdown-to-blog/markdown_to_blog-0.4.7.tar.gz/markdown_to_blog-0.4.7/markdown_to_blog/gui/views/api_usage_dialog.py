"""
Gemini API 사용량 확인 다이얼로그
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QProgressBar,
)
from PySide6.QtCore import Qt, QThread, Signal
from loguru import logger

from ...libs.gemini_usage import check_api_status, get_available_models


class ApiStatusCheckThread(QThread):
    """API 상태 확인을 백그라운드에서 수행하는 스레드"""

    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key

    def run(self):
        try:
            self.progress.emit("API 상태 확인 중...")
            result = check_api_status(api_key=self.api_key)
            self.finished.emit(result)
        except Exception as e:
            logger.exception("API 상태 확인 실패")
            self.error.emit(str(e))


class ApiUsageDialog(QDialog):
    """API 사용량 확인 다이얼로그"""

    def __init__(self, api_key=None, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.setWindowTitle("Gemini API 사용량 확인")
        self.setModal(False)  # 모달리스 다이얼로그
        self.resize(600, 500)
        self.status_thread = None
        self.setup_ui()
        self.check_status()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 상태 표시 영역
        status_group = QGroupBox("API 상태")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("확인 중...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 무한 진행 표시
        status_layout.addWidget(self.progress_bar)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 상세 정보 영역
        info_group = QGroupBox("상세 정보")
        info_layout = QVBoxLayout()

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("API 상태 정보가 여기에 표시됩니다...")
        info_layout.addWidget(self.info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 사용 가능한 모델 영역
        models_group = QGroupBox("사용 가능한 모델")
        models_layout = QVBoxLayout()

        self.models_text = QTextEdit()
        self.models_text.setReadOnly(True)
        self.models_text.setPlaceholderText("사용 가능한 모델 목록이 여기에 표시됩니다...")
        models_layout.addWidget(self.models_text)

        models_group.setLayout(models_layout)
        layout.addWidget(models_group)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.check_status)
        button_layout.addWidget(refresh_btn)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def check_status(self):
        """API 상태 확인 시작"""
        self.status_label.setText("확인 중...")
        self.progress_bar.setVisible(True)
        self.info_text.clear()
        self.models_text.clear()

        # 백그라운드 스레드에서 확인
        self.status_thread = ApiStatusCheckThread(api_key=self.api_key)
        self.status_thread.progress.connect(self.on_progress)
        self.status_thread.finished.connect(self.on_status_finished)
        self.status_thread.error.connect(self.on_status_error)
        self.status_thread.start()

    def on_progress(self, message: str):
        """진행 상황 업데이트"""
        logger.info(message)

    def on_status_finished(self, result: dict):
        """상태 확인 완료 처리"""
        self.progress_bar.setVisible(False)

        status = result.get("status", "unknown")
        message = result.get("message", "")
        models_count = result.get("models_count", 0)
        available_models = result.get("available_models", [])
        test_result = result.get("test_result", "")

        # 상태 표시
        if status == "valid":
            self.status_label.setText("✓ API 키가 유효합니다")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        elif status == "error":
            self.status_label.setText("✗ API 키 확인 실패")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        else:
            self.status_label.setText("? 상태 불명")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")

        # 상세 정보 표시
        info_lines = [
            f"상태: {status}",
            f"메시지: {message}",
            f"사용 가능한 모델 수: {models_count}개",
        ]
        if test_result:
            info_lines.append(f"테스트 결과: {test_result}")
        info_lines.append("")
        info_lines.append("참고: 실제 사용량 및 할당량은 Google Cloud Console에서 확인하실 수 있습니다.")
        info_lines.append("https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas")

        self.info_text.setPlainText("\n".join(info_lines))

        # 모델 목록 표시
        if available_models:
            model_lines = []
            for model in available_models:
                name = model.get("name", "Unknown")
                display_name = model.get("display_name", "")
                if display_name:
                    model_lines.append(f"• {name} ({display_name})")
                else:
                    model_lines.append(f"• {name}")
            self.models_text.setPlainText("\n".join(model_lines))
        else:
            self.models_text.setPlainText("사용 가능한 모델이 없습니다.")

    def on_status_error(self, error_message: str):
        """상태 확인 오류 처리"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("✗ 오류 발생")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        self.info_text.setPlainText(f"오류가 발생했습니다:\n\n{error_message}")

    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        if self.status_thread and self.status_thread.isRunning():
            self.status_thread.terminate()
            self.status_thread.wait()
        event.accept()

