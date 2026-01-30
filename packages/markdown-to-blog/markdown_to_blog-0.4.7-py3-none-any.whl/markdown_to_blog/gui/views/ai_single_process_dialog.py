"""
AI 단일 처리 다이얼로그
프롬프트와 입력을 결합하여 LLM에 보내고 응답을 받는 다이얼로그
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
    QSplitter,
    QWidget,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QClipboard
from loguru import logger
import json
import os
import asyncio

try:
    import google.generativeai as genai
except ImportError:
    logger.error("google-generativeai 패키지가 설치되지 않았습니다. 설치해주세요: uv sync")
    genai = None

try:
    from openai import OpenAI
except ImportError:
    logger.error("openai 패키지가 설치되지 않았습니다. 설치해주세요: uv sync")
    OpenAI = None

from ...libs.gemini_usage import get_available_models
from ..models import Setting


# OpenAI 기본 모델 목록
OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "o1-preview",
    "o1-mini",
]


class LLMRequestThread(QThread):
    """LLM 요청을 백그라운드에서 수행하는 스레드"""

    progress = Signal(str)
    finished = Signal(str)  # 응답 텍스트
    error = Signal(str)  # 오류 메시지

    def __init__(self, provider, model, prompt, api_key=None):
        super().__init__()
        self.provider = provider
        self.model = model
        self.prompt = prompt
        self.api_key = api_key

    def run(self):
        try:
            self.progress.emit("LLM에 요청 전송 중...")

            if self.provider == "gemini":
                if genai is None:
                    raise ImportError(
                        "google-generativeai 패키지가 설치되지 않았습니다. "
                        "다음 명령어로 설치해주세요: uv sync"
                    )

                # API 키 가져오기
                if not self.api_key or not self.api_key.strip():
                    self.api_key = os.getenv("GEMINI_API_KEY")
                if not self.api_key or not self.api_key.strip():
                    raise ValueError(
                        "GEMINI_API_KEY가 설정되지 않았습니다. "
                        "다이얼로그에서 API 키를 입력하거나 환경 변수를 설정해주세요."
                    )

                self.api_key = self.api_key.strip()
                genai.configure(api_key=self.api_key)
                generative_model = genai.GenerativeModel(self.model)

                logger.info(f"Gemini API 호출 시작...")
                logger.debug(f"사용 모델: {self.model}")
                logger.debug(f"프롬프트 길이: {len(self.prompt)}자")

                response = generative_model.generate_content(self.prompt)
                response_text = response.text.strip()

                logger.info("Gemini API 응답 수신 완료")
                logger.debug(f"응답 텍스트 길이: {len(response_text)}자")

                self.finished.emit(response_text)

            elif self.provider == "openai":
                if OpenAI is None:
                    raise ImportError(
                        "openai 패키지가 설치되지 않았습니다. "
                        "다음 명령어로 설치해주세요: uv sync"
                    )

                # API 키 가져오기
                if not self.api_key or not self.api_key.strip():
                    self.api_key = os.getenv("OPENAI_API_KEY")
                if not self.api_key or not self.api_key.strip():
                    raise ValueError(
                        "OPENAI_API_KEY가 설정되지 않았습니다. "
                        "다이얼로그에서 API 키를 입력하거나 환경 변수를 설정해주세요."
                    )

                self.api_key = self.api_key.strip()
                client = OpenAI(api_key=self.api_key)

                logger.info(f"OpenAI API 호출 시작...")
                logger.debug(f"사용 모델: {self.model}")
                logger.debug(f"프롬프트 길이: {len(self.prompt)}자")

                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": self.prompt}
                    ],
                    temperature=0.7,
                )

                response_text = response.choices[0].message.content.strip()

                logger.info("OpenAI API 응답 수신 완료")
                logger.debug(f"응답 텍스트 길이: {len(response_text)}자")

                self.finished.emit(response_text)
            else:
                raise ValueError(f"지원하지 않는 provider: {self.provider}")

        except Exception as e:
            logger.error(f"LLM 요청 중 오류 발생: {e}")
            self.error.emit(str(e))


class AISingleProcessDialog(QDialog):
    """AI 단일 처리 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 단일 처리")
        self.setModal(False)  # 모달리스 다이얼로그
        self.resize(1200, 800)
        self.request_thread = None
        self.loop = asyncio.new_event_loop()
        self.setup_ui()
        self.load_saved_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 모델 선택 영역
        model_group = QGroupBox("모델 선택")
        model_layout = QFormLayout()

        # Provider 선택
        provider_layout = QHBoxLayout()
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openai", "gemini"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        model_layout.addRow("Provider:", provider_layout)

        # Model 선택
        model_select_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_select_layout.addWidget(self.model_combo)

        # 모델 업데이트 버튼
        self.update_models_btn = QPushButton("모델 업데이트")
        self.update_models_btn.clicked.connect(self.update_models)
        model_select_layout.addWidget(self.update_models_btn)

        model_layout.addRow("Model:", model_select_layout)

        # API 키 입력
        api_key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("API 키를 입력하세요 (선택사항, 환경 변수 사용 가능)")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        api_key_layout.addWidget(self.api_key_edit)

        self.show_api_key_btn = QPushButton("표시")
        self.show_api_key_btn.setCheckable(True)
        self.show_api_key_btn.toggled.connect(self.toggle_api_key_visibility)
        api_key_layout.addWidget(self.show_api_key_btn)

        # API 키 변경 시 자동 저장
        self.api_key_edit.textChanged.connect(self.save_api_key)

        model_layout.addRow("API 키:", api_key_layout)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # 메인 영역 - Splitter 사용
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 왼쪽: 입력 영역
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 프롬프트 입력창
        prompt_label = QLabel("프롬프트 입력창")
        left_layout.addWidget(prompt_label)
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("프롬프트를 입력하세요...")
        self.prompt_edit.textChanged.connect(self.update_combined_prompt)
        left_layout.addWidget(self.prompt_edit)

        # Input 입력창
        input_label = QLabel("Input 입력창")
        left_layout.addWidget(input_label)
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("추가 입력을 입력하세요...")
        self.input_edit.textChanged.connect(self.update_combined_prompt)
        left_layout.addWidget(self.input_edit)

        splitter.addWidget(left_widget)

        # 중앙: 결합된 프롬프트 표시
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)

        combined_label = QLabel("결합된 프롬프트")
        center_layout.addWidget(combined_label)
        self.combined_edit = QTextEdit()
        self.combined_edit.setReadOnly(True)
        self.combined_edit.setPlaceholderText("프롬프트와 Input이 자동으로 합쳐집니다...")
        center_layout.addWidget(self.combined_edit)

        splitter.addWidget(center_widget)

        # 오른쪽: 응답 출력 영역
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        response_label = QLabel("응답 출력")
        right_layout.addWidget(response_label)
        self.response_edit = QTextEdit()
        self.response_edit.setReadOnly(True)
        self.response_edit.setPlaceholderText("받은 응답이 여기에 표시됩니다...")
        right_layout.addWidget(self.response_edit)

        # 복사 버튼
        copy_btn = QPushButton("결과 복사")
        copy_btn.clicked.connect(self.copy_response)
        right_layout.addWidget(copy_btn)

        splitter.addWidget(right_widget)

        # Splitter 비율 설정
        splitter.setSizes([400, 400, 400])

        # 보내기 버튼
        send_btn = QPushButton("보내기")
        send_btn.setStyleSheet("background-color: #0078d4; color: white; font-size: 14px; padding: 10px;")
        send_btn.clicked.connect(self.send_request)
        layout.addWidget(send_btn)

        # 초기 모델 로드
        self.on_provider_changed()

    def on_provider_changed(self):
        """Provider 변경 시 모델 목록 업데이트 및 API 키 로드"""
        provider = self.provider_combo.currentText()
        self.load_models_for_provider(provider)
        
        # Provider에 맞는 API 키 로드
        async def _load():
            try:
                if provider == "gemini":
                    setting = await Setting.get_or_none(key="gemini_api_key")
                elif provider == "openai":
                    setting = await Setting.get_or_none(key="openai_api_key")
                else:
                    return None
                
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

    def load_models_for_provider(self, provider):
        """Provider에 맞는 모델 목록 로드"""
        self.model_combo.clear()

        if provider == "openai":
            # OpenAI 모델 목록 로드
            saved_models = self.load_saved_models("openai")
            if saved_models:
                for model in saved_models:
                    self.model_combo.addItem(model)
            else:
                # 기본 모델 목록 사용
                for model in OPENAI_MODELS:
                    self.model_combo.addItem(model)
                # 기본값 설정
                if "gpt-4o-mini" in OPENAI_MODELS:
                    self.model_combo.setCurrentText("gpt-4o-mini")
        elif provider == "gemini":
            # Gemini 모델 목록 로드
            saved_models = self.load_saved_models("gemini")
            if saved_models:
                for model in saved_models:
                    self.model_combo.addItem(model)
            else:
                # 기본 모델 목록 사용
                default_models = [
                    "gemini-2.0-flash-exp",
                    "gemini-1.5-pro-latest",
                    "gemini-1.5-flash-latest",
                    "gemini-pro",
                ]
                for model in default_models:
                    self.model_combo.addItem(model)
                # 기본값 설정
                self.model_combo.setCurrentText("gemini-2.0-flash-exp")

    def update_models(self):
        """모델 목록 업데이트"""
        provider = self.provider_combo.currentText()
        api_key = self.api_key_edit.text().strip()

        if not api_key:
            # 환경 변수에서 가져오기 시도
            if provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
            elif provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            QMessageBox.warning(
                self,
                "경고",
                f"{provider.upper()} API 키를 먼저 입력하거나 환경 변수를 설정해주세요."
            )
            return

        try:
            if provider == "gemini":
                models = get_available_models(api_key=api_key)
                model_names = [model["name"] for model in models]
                self.model_combo.clear()
                for model_name in model_names:
                    self.model_combo.addItem(model_name)
                # 모델 목록 저장
                self.save_models("gemini", model_names)
                QMessageBox.information(
                    self,
                    "완료",
                    f"사용 가능한 Gemini 모델 {len(model_names)}개를 불러왔습니다."
                )
            elif provider == "openai":
                # OpenAI는 모델 리스트 API가 없으므로 기본 목록 사용
                # 사용자가 직접 입력한 모델도 추가 가능하도록 함
                QMessageBox.information(
                    self,
                    "정보",
                    "OpenAI는 모델 리스트 API를 제공하지 않습니다. "
                    "기본 모델 목록을 사용하거나 직접 입력해주세요."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"모델 목록을 가져올 수 없습니다:\n\n{str(e)}"
            )

    def update_combined_prompt(self):
        """프롬프트와 Input을 결합하여 표시"""
        prompt = self.prompt_edit.toPlainText()
        input_text = self.input_edit.toPlainText()

        # 프롬프트에 {input_text}가 있으면 치환, 없으면 그냥 합치기
        if "{input_text}" in prompt:
            combined = prompt.replace("{input_text}", input_text)
        else:
            if prompt and input_text:
                combined = f"{prompt}\n\n{input_text}"
            elif prompt:
                combined = prompt
            elif input_text:
                combined = input_text
            else:
                combined = ""

        self.combined_edit.setPlainText(combined)

    def send_request(self):
        """LLM에 요청 전송"""
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText().strip()
        combined_prompt = self.combined_edit.toPlainText().strip()

        if not model:
            QMessageBox.warning(self, "경고", "모델을 선택해주세요.")
            return

        if not combined_prompt:
            QMessageBox.warning(self, "경고", "프롬프트를 입력해주세요.")
            return

        api_key = self.api_key_edit.text().strip()
        if not api_key:
            # 환경 변수에서 가져오기 시도
            if provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
            elif provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            QMessageBox.warning(
                self,
                "경고",
                f"{provider.upper()} API 키를 입력하거나 환경 변수를 설정해주세요."
            )
            return

        # 응답 영역 초기화
        self.response_edit.clear()
        self.response_edit.setPlainText("요청 전송 중...")

        # 스레드 생성 및 시작
        self.request_thread = LLMRequestThread(provider, model, combined_prompt, api_key)
        self.request_thread.progress.connect(self.on_progress)
        self.request_thread.finished.connect(self.on_finished)
        self.request_thread.error.connect(self.on_error)
        self.request_thread.start()

    def on_progress(self, message):
        """진행 상황 업데이트"""
        self.response_edit.setPlainText(message)

    def on_finished(self, response_text):
        """요청 완료"""
        self.response_edit.setPlainText(response_text)
        QMessageBox.information(self, "완료", "응답을 받았습니다.")

    def on_error(self, error_message):
        """오류 발생"""
        self.response_edit.setPlainText(f"오류 발생:\n{error_message}")
        QMessageBox.critical(self, "오류", f"요청 중 오류가 발생했습니다:\n\n{error_message}")

    def copy_response(self):
        """응답 결과 복사"""
        response_text = self.response_edit.toPlainText()
        if not response_text:
            QMessageBox.warning(self, "경고", "복사할 내용이 없습니다.")
            return

        clipboard = QClipboard()
        clipboard.setText(response_text)
        QMessageBox.information(self, "완료", "응답이 클립보드에 복사되었습니다.")

    def toggle_api_key_visibility(self, checked):
        """API 키 표시/숨김 토글"""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_api_key_btn.setText("숨김")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_api_key_btn.setText("표시")

    def load_saved_settings(self):
        """저장된 설정 불러오기"""
        async def _load():
            settings = {}
            all_settings = await Setting.all()
            for setting in all_settings:
                settings[setting.key] = setting.value
            return settings

        try:
            settings = self.loop.run_until_complete(_load())

            # Provider 로드
            provider = settings.get("ai_single_process_provider", "gemini")
            if provider in ["openai", "gemini"]:
                self.provider_combo.setCurrentText(provider)

            # API 키 로드
            provider = self.provider_combo.currentText()
            if provider == "gemini":
                api_key = settings.get("gemini_api_key", "")
            else:
                api_key = settings.get("openai_api_key", "")
            if api_key:
                self.api_key_edit.setText(api_key)

            # 모델 로드
            self.on_provider_changed()
            model = settings.get("ai_single_process_model", "")
            if model:
                self.model_combo.setCurrentText(model)

        except Exception as e:
            logger.error(f"설정 불러오기 실패: {e}")

    def save_api_key(self):
        """API 키 저장 (입력 시 자동 저장)"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            return  # 빈 값이면 저장하지 않음

        provider = self.provider_combo.currentText()

        async def _save():
            try:
                if provider == "gemini":
                    await Setting.update_or_create(
                        key="gemini_api_key",
                        defaults={"value": api_key}
                    )
                elif provider == "openai":
                    await Setting.update_or_create(
                        key="openai_api_key",
                        defaults={"value": api_key}
                    )
                logger.info(f"{provider} API 키가 저장되었습니다.")
            except Exception as e:
                logger.error(f"API 키 저장 실패: {e}")

        try:
            self.loop.run_until_complete(_save())
        except Exception as e:
            logger.error(f"API 키 저장 중 오류: {e}")

    def save_settings(self):
        """설정 저장"""
        async def _save():
            provider = self.provider_combo.currentText()
            model = self.model_combo.currentText()

            await Setting.update_or_create(
                key="ai_single_process_provider",
                defaults={"value": provider}
            )
            await Setting.update_or_create(
                key="ai_single_process_model",
                defaults={"value": model}
            )

        try:
            self.loop.run_until_complete(_save())
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")

    def load_saved_models(self, provider):
        """저장된 모델 목록 불러오기"""
        async def _load():
            try:
                key = f"ai_single_process_models_{provider}"
                setting = await Setting.get_or_none(key=key)
                if setting:
                    return json.loads(setting.value)
                return None
            except Exception as e:
                logger.error(f"모델 목록 불러오기 실패: {e}")
                return None

        try:
            return self.loop.run_until_complete(_load())
        except Exception as e:
            logger.error(f"모델 목록 불러오기 중 오류: {e}")
            return None

    def save_models(self, provider, models):
        """모델 목록 저장"""
        async def _save():
            try:
                key = f"ai_single_process_models_{provider}"
                await Setting.update_or_create(
                    key=key,
                    defaults={"value": json.dumps(models)}
                )
            except Exception as e:
                logger.error(f"모델 목록 저장 실패: {e}")

        try:
            self.loop.run_until_complete(_save())
        except Exception as e:
            logger.error(f"모델 목록 저장 중 오류: {e}")

    def closeEvent(self, event):
        """다이얼로그 닫을 때 설정 저장"""
        self.save_settings()
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.terminate()
            self.request_thread.wait()
        event.accept()
