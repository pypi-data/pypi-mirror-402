"""
단계별 워크플로우 다이얼로그
각 단계별 프롬프트를 순차적으로 적용하여 블로그 글을 생성합니다.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QComboBox,
    QGroupBox,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QScrollArea,
    QWidget,
    QCheckBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from loguru import logger
import json
import os

try:
    import google.generativeai as genai
except ImportError:
    logger.error("google-generativeai 패키지가 설치되지 않았습니다. 설치해주세요: uv sync")
    genai = None

from ...libs.gemini_usage import check_api_status, get_available_models
from ..models import Setting
import asyncio


class WorkflowStepThread(QThread):
    """단계별 글 생성을 백그라운드에서 수행하는 스레드"""

    progress = Signal(str)
    finished = Signal(str, int)  # (결과 텍스트, 단계 번호)
    error = Signal(str, int)  # (오류 메시지, 단계 번호)

    def __init__(self, step_number, prompt, input_text, api_key=None, model=None):
        super().__init__()
        self.step_number = step_number
        self.prompt = prompt
        self.input_text = input_text
        self.api_key = api_key
        self.model = model or "gemini-2.0-flash-exp"

    def run(self):
        try:
            self.progress.emit(f"{self.step_number}단계 진행 중...")
            
            if genai is None:
                raise ImportError(
                    "google-generativeai 패키지가 설치되지 않았습니다. "
                    "다음 명령어로 설치해주세요: uv sync"
                )

            # API 키 가져오기 (빈 문자열도 None으로 처리)
            if not self.api_key or not self.api_key.strip():
                self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key or not self.api_key.strip():
                raise ValueError(
                    "GEMINI_API_KEY가 설정되지 않았습니다. "
                    "다이얼로그에서 API 키를 입력하거나 환경 변수를 설정해주세요."
                )
            
            # API 키 앞뒤 공백 제거
            self.api_key = self.api_key.strip()

            # Gemini API 클라이언트 초기화
            genai.configure(api_key=self.api_key)
            generative_model = genai.GenerativeModel(self.model)

            # 프롬프트에 입력 텍스트 치환
            full_prompt = self.prompt.format(input_text=self.input_text)

            # API 호출
            logger.info(f"{self.step_number}단계 Gemini API 호출 시작...")
            logger.debug(f"사용 모델: {self.model}")
            logger.debug(f"프롬프트 길이: {len(full_prompt)}자")
            logger.info(f"{self.step_number}단계 프롬프트:\n{full_prompt}")

            response = generative_model.generate_content(full_prompt)
            response_text = response.text.strip()

            # API 응답 로깅
            logger.info(f"{self.step_number}단계 Gemini API 응답 수신 완료")
            logger.debug(f"응답 텍스트 길이: {len(response_text)}자")
            logger.info(f"{self.step_number}단계 응답:\n{response_text}")

            self.finished.emit(response_text, self.step_number)
        except Exception as e:
            logger.exception(f"{self.step_number}단계 처리 실패")
            self.error.emit(str(e), self.step_number)


class WorkflowStepWidget(QWidget):
    """단계별 위젯"""

    def __init__(self, step_number, parent=None):
        super().__init__(parent)
        self.step_number = step_number
        self.result_text = ""
        self.thread = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 단계 헤더
        header_layout = QHBoxLayout()
        step_label = QLabel(f"{self.step_number}단계")
        step_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(step_label)
        header_layout.addStretch()

        self.run_step_btn = QPushButton(f"{self.step_number}단계 실행")
        self.run_step_btn.clicked.connect(self.run_step_clicked)
        header_layout.addWidget(self.run_step_btn)

        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # 프롬프트 입력
        prompt_label = QLabel("프롬프트:")
        prompt_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(prompt_label)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(f"{self.step_number}단계 프롬프트를 입력하세요. {{input_text}} 변수를 사용할 수 있습니다.")
        self.prompt_edit.setMinimumHeight(100)
        layout.addWidget(self.prompt_edit)

        # 결과 출력
        result_label = QLabel("결과:")
        result_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(result_label)

        self.result_edit = QTextEdit()
        self.result_edit.setPlaceholderText(f"{self.step_number}단계 결과가 여기에 표시됩니다...")
        self.result_edit.setReadOnly(True)
        self.result_edit.setMinimumHeight(150)
        layout.addWidget(self.result_edit)

        # 진행 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def set_prompt(self, prompt: str):
        """프롬프트 설정"""
        self.prompt_edit.setPlainText(prompt)

    def get_prompt(self) -> str:
        """프롬프트 가져오기"""
        return self.prompt_edit.toPlainText().strip()

    def set_result(self, text: str):
        """결과 설정"""
        self.result_text = text
        self.result_edit.setPlainText(text)
        self.status_label.setText("완료")
        self.status_label.setStyleSheet("color: green;")

    def get_result(self) -> str:
        """결과 가져오기"""
        return self.result_text

    def run_step_clicked(self):
        """단계 실행 버튼 클릭 핸들러"""
        # 부모 다이얼로그에서 API 키와 모델 가져오기
        parent_widget = self.parent()
        while parent_widget and not isinstance(parent_widget, WorkflowDialog):
            parent_widget = parent_widget.parent()
        
        api_key = None
        model = None
        if parent_widget and isinstance(parent_widget, WorkflowDialog):
            api_key = parent_widget.get_api_key()
            model = parent_widget.model_combo.currentText().strip()
            if not model:
                model = "gemini-2.0-flash-exp"
        
        # API 키가 없으면 경고
        if not api_key:
            QMessageBox.warning(self, "경고", "API 키를 입력해주세요.")
            return
        
        self.run_step(api_key=api_key, model=model)

    def run_step(self, input_text: str = None, api_key: str = None, model: str = None):
        """단계 실행"""
        if input_text is None:
            # 이전 단계 결과 사용
            if self.step_number > 1:
                parent_widget = self.parent()
                while parent_widget and not isinstance(parent_widget, WorkflowDialog):
                    parent_widget = parent_widget.parent()
                if parent_widget and hasattr(parent_widget, 'get_previous_step_result'):
                    input_text = parent_widget.get_previous_step_result(self.step_number - 1)
                else:
                    QMessageBox.warning(self, "경고", "이전 단계 결과가 없습니다.")
                    return
            else:
                # 첫 번째 단계는 주제 사용
                parent_widget = self.parent()
                while parent_widget and not isinstance(parent_widget, WorkflowDialog):
                    parent_widget = parent_widget.parent()
                if parent_widget and hasattr(parent_widget, 'topic_edit'):
                    input_text = parent_widget.topic_edit.text().strip()
                if not input_text:
                    QMessageBox.warning(self, "경고", "주제를 입력해주세요.")
                    return

        prompt = self.get_prompt()
        if not prompt:
            QMessageBox.warning(self, "경고", "프롬프트를 입력해주세요.")
            return

        # UI 업데이트
        self.run_step_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("실행 중...")
        self.status_label.setStyleSheet("color: blue;")
        self.result_edit.clear()

        # 백그라운드 스레드에서 실행
        self.thread = WorkflowStepThread(
            step_number=self.step_number,
            prompt=prompt,
            input_text=input_text,
            api_key=api_key,
            model=model,
        )
        self.thread.progress.connect(self.on_progress)
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_progress(self, message: str):
        """진행 상황 업데이트"""
        logger.info(message)

    def on_finished(self, result: str, step_number: int):
        """완료 처리"""
        self.progress_bar.setVisible(False)
        self.run_step_btn.setEnabled(True)
        self.set_result(result)

    def on_error(self, error_message: str, step_number: int):
        """오류 처리"""
        self.progress_bar.setVisible(False)
        self.run_step_btn.setEnabled(True)
        self.status_label.setText("오류")
        self.status_label.setStyleSheet("color: red;")
        self.result_edit.setPlainText(f"오류: {error_message}")


class WorkflowDialog(QDialog):
    """단계별 워크플로우 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("단계별 워크플로우")
        self.setModal(False)  # 모달리스 다이얼로그
        self.resize(1400, 900)
        self.steps = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 상단 설정 영역
        settings_group = QGroupBox("설정")
        settings_layout = QFormLayout()

        # Gemini API 키
        api_key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("GEMINI_API_KEY를 입력하세요 (선택사항, 환경 변수 사용 가능)")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.show_api_key_btn = QPushButton("표시")
        self.show_api_key_btn.setCheckable(True)
        self.show_api_key_btn.toggled.connect(self.toggle_api_key_visibility)
        self.usage_check_btn = QPushButton("사용량 체크")
        self.usage_check_btn.clicked.connect(self.check_api_usage)
        self.clear_api_key_btn = QPushButton("Clear")
        self.clear_api_key_btn.clicked.connect(self.clear_api_key)
        api_key_layout.addWidget(self.api_key_edit)
        api_key_layout.addWidget(self.show_api_key_btn)
        api_key_layout.addWidget(self.usage_check_btn)
        api_key_layout.addWidget(self.clear_api_key_btn)
        settings_layout.addRow("Gemini API 키:", api_key_layout)
        
        # API 키 변경 시 자동 저장
        self.api_key_edit.textChanged.connect(self.save_api_key)

        # 모델 선택
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest",
            "gemini-pro",
        ])
        self.model_combo.setCurrentText("gemini-2.0-flash-exp")
        refresh_models_btn = QPushButton("모델 목록 새로고침")
        refresh_models_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(refresh_models_btn)
        settings_layout.addRow("모델:", model_layout)

        # 주제 입력
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("블로그 글 주제를 입력하세요")
        settings_layout.addRow("주제:", self.topic_edit)

        # 단계 개수
        steps_layout = QHBoxLayout()
        self.steps_count_spin = QSpinBox()
        self.steps_count_spin.setMinimum(1)
        self.steps_count_spin.setMaximum(10)
        self.steps_count_spin.setValue(3)
        steps_layout.addWidget(self.steps_count_spin)
        steps_layout.addWidget(QLabel("개"))
        add_steps_btn = QPushButton("단계 추가")
        add_steps_btn.clicked.connect(self.add_steps)
        steps_layout.addWidget(add_steps_btn)
        reset_steps_btn = QPushButton("단계 초기화")
        reset_steps_btn.clicked.connect(self.reset_steps)
        steps_layout.addWidget(reset_steps_btn)
        settings_layout.addRow("단계 개수:", steps_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # 실행 버튼
        button_layout = QHBoxLayout()
        self.run_all_btn = QPushButton("모든 단계 실행")
        self.run_all_btn.clicked.connect(self.run_all_steps)
        self.run_all_btn.setEnabled(False)
        button_layout.addWidget(self.run_all_btn)

        self.copy_final_btn = QPushButton("최종 결과 복사")
        self.copy_final_btn.clicked.connect(self.copy_final_result)
        self.copy_final_btn.setEnabled(False)
        button_layout.addWidget(self.copy_final_btn)

        button_layout.addStretch()

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # 단계별 영역 (스크롤 가능)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.steps_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 초기 단계 생성
        self.create_steps()

    def toggle_api_key_visibility(self, checked: bool):
        """API 키 표시/숨김 토글"""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_api_key_btn.setText("숨김")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_api_key_btn.setText("표시")

    def get_api_key(self) -> str:
        """입력된 API 키 반환"""
        api_key = self.api_key_edit.text().strip()
        return api_key if api_key else None

    def load_saved_api_key(self):
        """저장된 API 키 불러오기"""
        async def _load():
            try:
                setting = await Setting.get_or_none(key="gemini_api_key")
                if setting:
                    return setting.value
                return None
            except Exception as e:
                logger.error(f"API 키 불러오기 실패: {e}")
                return None
        
        try:
            api_key = self.loop.run_until_complete(_load())
            if api_key:
                self.api_key_edit.setText(api_key)
        except Exception as e:
            logger.error(f"API 키 불러오기 중 오류: {e}")

    def save_api_key(self):
        """API 키 저장 (입력 시 자동 저장)"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            return  # 빈 값이면 저장하지 않음
        
        async def _save():
            try:
                await Setting.update_or_create(
                    key="gemini_api_key",
                    defaults={"value": api_key}
                )
                logger.info("API 키가 저장되었습니다.")
            except Exception as e:
                logger.error(f"API 키 저장 실패: {e}")
        
        try:
            self.loop.run_until_complete(_save())
        except Exception as e:
            logger.error(f"API 키 저장 중 오류: {e}")

    def clear_api_key(self):
        """저장된 API 키 삭제"""
        reply = QMessageBox.question(
            self,
            "확인",
            "저장된 API 키를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            async def _delete():
                try:
                    setting = await Setting.get_or_none(key="gemini_api_key")
                    if setting:
                        await setting.delete()
                        logger.info("API 키가 삭제되었습니다.")
                except Exception as e:
                    logger.error(f"API 키 삭제 실패: {e}")
            
            try:
                self.loop.run_until_complete(_delete())
                self.api_key_edit.clear()
                QMessageBox.information(self, "완료", "저장된 API 키가 삭제되었습니다.")
            except Exception as e:
                logger.error(f"API 키 삭제 중 오류: {e}")
                QMessageBox.critical(self, "오류", f"API 키 삭제 중 오류가 발생했습니다:\n\n{str(e)}")

    def refresh_models(self):
        """사용 가능한 모델 목록 새로고침"""
        api_key = self.get_api_key()
        if not api_key:
            QMessageBox.warning(self, "경고", "API 키를 먼저 입력해주세요.")
            return

        try:
            models = get_available_models(api_key=api_key)
            self.model_combo.clear()
            for model in models:
                self.model_combo.addItem(model["name"], model["display_name"])
            QMessageBox.information(self, "완료", f"사용 가능한 모델 {len(models)}개를 불러왔습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"모델 목록을 가져올 수 없습니다:\n\n{str(e)}")

    def check_api_usage(self):
        """API 사용량 확인 다이얼로그 열기"""
        from .api_usage_dialog import ApiUsageDialog
        api_key = self.get_api_key()
        dialog = ApiUsageDialog(api_key=api_key, parent=self)
        dialog.show()  # 모달리스 다이얼로그

    def create_steps(self):
        """초기 단계 위젯 생성"""
        # 기존 단계 제거
        for step in self.steps:
            step.setParent(None)
        self.steps.clear()

        # 새 단계 생성
        num_steps = self.steps_count_spin.value()
        for i in range(1, num_steps + 1):
            step_widget = WorkflowStepWidget(step_number=i, parent=self)
            # 기본 프롬프트 설정
            default_prompt = self.get_default_prompt(i)
            step_widget.set_prompt(default_prompt)
            self.steps.append(step_widget)
            self.steps_layout.addWidget(step_widget)

        self.run_all_btn.setEnabled(True)

    def add_steps(self):
        """새 단계 추가 (기존 단계 유지)"""
        num_new_steps = self.steps_count_spin.value()
        current_step_count = len(self.steps)
        
        if num_new_steps <= 0:
            QMessageBox.warning(self, "경고", "추가할 단계 개수를 입력해주세요.")
            return
        
        # 새 단계 생성
        for i in range(1, num_new_steps + 1):
            step_number = current_step_count + i
            step_widget = WorkflowStepWidget(step_number=step_number, parent=self)
            # 기본 프롬프트 설정
            default_prompt = self.get_default_prompt(step_number)
            step_widget.set_prompt(default_prompt)
            self.steps.append(step_widget)
            self.steps_layout.addWidget(step_widget)

        self.run_all_btn.setEnabled(True)
        QMessageBox.information(self, "완료", f"{num_new_steps}개의 단계가 추가되었습니다.")

    def reset_steps(self):
        """모든 단계 초기화"""
        reply = QMessageBox.question(
            self,
            "확인",
            "모든 단계를 초기화하시겠습니까? (입력한 내용이 모두 삭제됩니다)",
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            self.create_steps()

    def get_default_prompt(self, step_number: int) -> str:
        """기본 프롬프트 반환"""
        if step_number == 1:
            return """다음 주제에 대해 블로그 글의 초안을 작성해주세요.

주제: {input_text}

요구사항:
- 도입부(호기심 유발)
- 본론 (3~4개의 소제목 + 단락 구조)
- 결론(요약 + 행동 유도 CTA)

마크다운 형식으로 작성해주세요."""
        elif step_number == 2:
            return """다음 블로그 글 초안을 개선해주세요.

{input_text}

요구사항:
- SEO 최적화 (키워드 자연스럽게 삽입)
- 문체 다듬기
- 가독성 향상
- 구체적인 예시 추가

마크다운 형식으로 개선된 글을 작성해주세요."""
        else:
            return """다음 블로그 글을 추가로 개선해주세요.

{input_text}

요구사항:
- 내용 보완
- 문장 다듬기
- 최종 검수

마크다운 형식으로 최종 글을 작성해주세요."""

    def get_previous_step_result(self, step_number: int) -> str:
        """이전 단계 결과 가져오기"""
        if step_number == 0:
            # 첫 번째 단계는 주제 사용
            return self.topic_edit.text().strip()
        elif 1 <= step_number <= len(self.steps):
            return self.steps[step_number - 1].get_result()
        return ""

    def run_all_steps(self):
        """모든 단계를 연쇄적으로 실행"""
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "경고", "주제를 입력해주세요.")
            return

        api_key = self.get_api_key()
        model = self.model_combo.currentText().strip()

        # 첫 번째 단계부터 순차 실행
        self.run_step_chain(1, topic, api_key, model)

    def run_step_chain(self, step_number: int, input_text: str, api_key: str, model: str):
        """단계를 연쇄적으로 실행"""
        if step_number > len(self.steps):
            # 모든 단계 완료
            self.copy_final_btn.setEnabled(True)
            QMessageBox.information(self, "완료", "모든 단계가 완료되었습니다!")
            return

        step_widget = self.steps[step_number - 1]

        def on_step_finished(result: str, completed_step: int):
            """단계 완료 시 다음 단계 실행"""
            if completed_step == step_number:
                # 다음 단계 실행
                self.run_step_chain(step_number + 1, result, api_key, model)

        def on_step_error(error_message: str, error_step: int):
            """단계 오류 시 중단"""
            QMessageBox.critical(
                self,
                "오류",
                f"{error_step}단계에서 오류가 발생했습니다:\n\n{error_message}",
            )

        # 단계 실행을 위한 프롬프트 확인
        prompt = step_widget.get_prompt()
        if not prompt:
            QMessageBox.warning(self, "경고", f"{step_number}단계 프롬프트를 입력해주세요.")
            return

        # UI 업데이트
        step_widget.run_step_btn.setEnabled(False)
        step_widget.progress_bar.setVisible(True)
        step_widget.progress_bar.setRange(0, 0)
        step_widget.status_label.setText("실행 중...")
        step_widget.status_label.setStyleSheet("color: blue;")
        step_widget.result_edit.clear()

        # 스레드 생성 및 시그널 연결
        step_widget.thread = WorkflowStepThread(
            step_number=step_number,
            prompt=prompt,
            input_text=input_text,
            api_key=api_key,
            model=model,
        )
        # 기본 시그널 연결 (UI 업데이트용)
        step_widget.thread.progress.connect(step_widget.on_progress)
        step_widget.thread.finished.connect(step_widget.on_finished)
        step_widget.thread.error.connect(step_widget.on_error)
        # 연쇄 실행용 시그널 연결
        step_widget.thread.finished.connect(on_step_finished)
        step_widget.thread.error.connect(on_step_error)
        
        # 스레드 시작
        step_widget.thread.start()

    def copy_final_result(self):
        """최종 결과를 클립보드에 복사"""
        if not self.steps:
            return

        final_result = self.steps[-1].get_result()
        if not final_result:
            QMessageBox.warning(self, "경고", "최종 결과가 없습니다.")
            return

        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(final_result)
        QMessageBox.information(self, "완료", "최종 결과가 클립보드에 복사되었습니다!")

    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        # 실행 중인 스레드 종료
        for step in self.steps:
            if step.thread and step.thread.isRunning():
                step.thread.terminate()
                step.thread.wait()
        event.accept()

