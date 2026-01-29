"""
블로그 글 자동 생성 다이얼로그
모달리스 다이얼로그로 블로그 글을 생성하고 편집할 수 있습니다.
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
    QFileDialog,
    QCheckBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from loguru import logger
from pathlib import Path

from ...libs.blog_generator import generate_blog_post, generate_keywords
from ...libs.gemini_usage import check_api_status, get_available_models
from ...libs.blogger import upload_to_blogspot, get_blogid, get_datetime_after, get_datetime_after_hour
from ...libs.markdown import read_first_header_from_md
from ...libs.blogger import upload_to_blogspot, get_blogid, get_datetime_after, get_datetime_after_hour
from ...libs.markdown import read_first_header_from_md


class BlogGeneratorThread(QThread):
    """블로그 글 생성을 백그라운드에서 수행하는 스레드"""

    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, topic, tone, main_keywords, sub_keywords, api_key=None, model="gemini-2.0-flash-exp"):
        super().__init__()
        self.topic = topic
        self.tone = tone
        self.main_keywords = main_keywords
        self.sub_keywords = sub_keywords
        self.api_key = api_key
        self.model = model

    def run(self):
        try:
            self.progress.emit("블로그 글 생성 중...")
            result = generate_blog_post(
                topic=self.topic,
                tone=self.tone,
                main_keywords=self.main_keywords,
                sub_keywords=self.sub_keywords,
                api_key=self.api_key,
                model=self.model,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("블로그 글 생성 실패")
            self.error.emit(str(e))


class KeywordGeneratorThread(QThread):
    """키워드 생성을 백그라운드에서 수행하는 스레드"""

    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, topic, api_key=None, model=None):
        super().__init__()
        self.topic = topic
        self.api_key = api_key
        self.model = model or "gemini-2.0-flash-exp"

    def run(self):
        try:
            self.progress.emit("키워드 생성 중...")
            result = generate_keywords(topic=self.topic, api_key=self.api_key, model=self.model)
            self.finished.emit(result)
        except Exception as e:
            logger.exception("키워드 생성 실패")
            self.error.emit(str(e))


class BlogGeneratorDialog(QDialog):
    """블로그 글 자동 생성 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("블로그 글 자동 생성")
        self.setModal(False)  # 모달리스 다이얼로그
        self.resize(1200, 800)
        self.generator_thread = None
        self.keyword_thread = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 입력 섹션
        input_group = QGroupBox("입력 정보")
        input_layout = QFormLayout()

        # Gemini API 키
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("GEMINI_API_KEY를 입력하세요 (선택사항, 환경 변수 사용 가능)")
        self.api_key_edit.setEchoMode(QLineEdit.Password)  # 비밀번호 모드로 표시
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(self.api_key_edit)
        self.show_api_key_btn = QPushButton("표시")
        self.show_api_key_btn.setCheckable(True)
        self.show_api_key_btn.toggled.connect(self.toggle_api_key_visibility)
        self.usage_check_btn = QPushButton("사용량 체크")
        self.usage_check_btn.clicked.connect(self.check_api_usage)
        api_key_layout.addWidget(self.show_api_key_btn)
        api_key_layout.addWidget(self.usage_check_btn)
        input_layout.addRow("Gemini API 키:", api_key_layout)

        # 모델 선택
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)  # 직접 입력도 가능하도록
        self.model_combo.addItems([
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest",
            "gemini-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ])
        self.model_combo.setCurrentText("gemini-2.0-flash-exp")
        model_layout.addWidget(self.model_combo)
        refresh_models_btn = QPushButton("모델 목록 새로고침")
        refresh_models_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(refresh_models_btn)
        input_layout.addRow("모델:", model_layout)

        # 주제
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("예: Python으로 웹 크롤링하기")
        input_layout.addRow("주제:", self.topic_edit)

        # 톤
        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["친근", "전문", "유머러스", "차분"])
        input_layout.addRow("톤:", self.tone_combo)

        # SEO 메인 키워드
        main_keyword_layout = QHBoxLayout()
        self.main_keyword1_edit = QLineEdit()
        self.main_keyword1_edit.setPlaceholderText("메인 키워드 1")
        self.main_keyword2_edit = QLineEdit()
        self.main_keyword2_edit.setPlaceholderText("메인 키워드 2 (선택)")
        self.main_keyword_btn = QPushButton("자동 생성")
        self.main_keyword_btn.clicked.connect(self.generate_main_keywords)
        main_keyword_layout.addWidget(self.main_keyword1_edit)
        main_keyword_layout.addWidget(QLabel("/"))
        main_keyword_layout.addWidget(self.main_keyword2_edit)
        main_keyword_layout.addWidget(self.main_keyword_btn)
        input_layout.addRow("SEO 메인 키워드:", main_keyword_layout)

        # SEO 서브 키워드
        sub_keyword_layout = QHBoxLayout()
        self.sub_keyword1_edit = QLineEdit()
        self.sub_keyword1_edit.setPlaceholderText("서브 키워드 1")
        self.sub_keyword2_edit = QLineEdit()
        self.sub_keyword2_edit.setPlaceholderText("서브 키워드 2")
        self.sub_keyword3_edit = QLineEdit()
        self.sub_keyword3_edit.setPlaceholderText("서브 키워드 3 (선택)")
        self.sub_keyword_btn = QPushButton("자동 생성")
        self.sub_keyword_btn.clicked.connect(self.generate_sub_keywords)
        sub_keyword_layout.addWidget(self.sub_keyword1_edit)
        sub_keyword_layout.addWidget(QLabel("/"))
        sub_keyword_layout.addWidget(self.sub_keyword2_edit)
        sub_keyword_layout.addWidget(QLabel("/"))
        sub_keyword_layout.addWidget(self.sub_keyword3_edit)
        sub_keyword_layout.addWidget(self.sub_keyword_btn)
        input_layout.addRow("SEO 서브 키워드:", sub_keyword_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 생성 버튼
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("글 생성하기")
        self.generate_btn.clicked.connect(self.generate_blog_post)
        button_layout.addWidget(self.generate_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)

        button_layout.addStretch()

        self.save_btn = QPushButton("마크다운 저장")
        self.save_btn.clicked.connect(self.save_markdown)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)

        self.publish_btn = QPushButton("블로그 발행")
        self.publish_btn.clicked.connect(self.publish_to_blog)
        self.publish_btn.setEnabled(False)
        button_layout.addWidget(self.publish_btn)

        layout.addLayout(button_layout)

        # 발행 옵션 섹션
        publish_options_group = QGroupBox("발행 옵션")
        publish_options_layout = QFormLayout()

        # 블로그 ID
        self.blog_id_edit = QLineEdit()
        self.blog_id_edit.setPlaceholderText("블로그 ID (비워두면 기본값 사용)")
        publish_options_layout.addRow("Blog ID:", self.blog_id_edit)

        # 드래프트 모드
        self.draft_checkbox = QCheckBox("드래프트로 저장")
        publish_options_layout.addRow("", self.draft_checkbox)

        # 발행 시점
        publish_time_layout = QHBoxLayout()
        self.publish_time_combo = QComboBox()
        self.publish_time_combo.addItems(["즉시", "1분 후", "10분 후", "1시간 후", "1일 후", "1주 후", "1개월 후"])
        self.publish_time_combo.setCurrentText("즉시")
        self.publish_time_hour_spin = QSpinBox()
        self.publish_time_hour_spin.setMinimum(0)
        self.publish_time_hour_spin.setMaximum(999)
        self.publish_time_hour_spin.setSuffix(" 시간 후")
        self.publish_time_hour_spin.setValue(0)
        self.publish_time_hour_spin.setEnabled(False)
        publish_time_layout.addWidget(self.publish_time_combo)
        publish_time_layout.addWidget(QLabel("또는"))
        publish_time_layout.addWidget(self.publish_time_hour_spin)
        publish_options_layout.addRow("발행 시점:", publish_time_layout)

        # 라벨
        self.labels_edit = QLineEdit()
        self.labels_edit.setPlaceholderText("라벨 (쉼표로 구분, 예: 파이썬, 프로그래밍)")
        publish_options_layout.addRow("라벨:", self.labels_edit)

        # 설명 (SEO)
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("검색 엔진용 메타 설명 (SEO)")
        publish_options_layout.addRow("설명:", self.description_edit)

        # 썸네일
        self.thumbnail_edit = QLineEdit()
        self.thumbnail_edit.setPlaceholderText("썸네일 이미지 URL")
        publish_options_layout.addRow("썸네일:", self.thumbnail_edit)

        publish_options_group.setLayout(publish_options_layout)
        layout.addWidget(publish_options_group)

        # 결과 섹션 (스플리터 사용)
        splitter = QSplitter(Qt.Horizontal)

        # 마크다운 결과
        result_group = QGroupBox("생성된 블로그 글 (마크다운)")
        result_layout = QVBoxLayout()
        self.markdown_edit = QTextEdit()
        self.markdown_edit.setPlaceholderText("생성된 블로그 글이 여기에 표시됩니다...")
        self.markdown_edit.setReadOnly(False)  # 편집 가능
        result_layout.addWidget(self.markdown_edit)
        result_group.setLayout(result_layout)
        splitter.addWidget(result_group)

        # SEO 요약 및 검수 지점
        summary_group = QGroupBox("SEO 요약 및 검수 지점")
        summary_layout = QVBoxLayout()

        # SEO 요약
        seo_label = QLabel("SEO 키워드 적용 요약:")
        seo_label.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(seo_label)
        self.seo_summary_edit = QTextEdit()
        self.seo_summary_edit.setPlaceholderText("SEO 키워드 적용 요약이 여기에 표시됩니다...")
        self.seo_summary_edit.setReadOnly(True)
        summary_layout.addWidget(self.seo_summary_edit)

        # 검수 지점
        review_label = QLabel("검수 지점 요약:")
        review_label.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(review_label)
        self.review_points_edit = QTextEdit()
        self.review_points_edit.setPlaceholderText("검수 지점이 여기에 표시됩니다...")
        self.review_points_edit.setReadOnly(True)
        summary_layout.addWidget(self.review_points_edit)

        summary_group.setLayout(summary_layout)
        splitter.addWidget(summary_group)

        # 스플리터 비율 설정 (70:30)
        splitter.setSizes([840, 360])
        layout.addWidget(splitter)

        # 닫기 버튼
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def toggle_api_key_visibility(self, checked: bool):
        """API 키 표시/숨김 토글"""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_api_key_btn.setText("숨김")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_api_key_btn.setText("표시")

    def get_api_key(self) -> str:
        """입력된 API 키 반환 (없으면 None)"""
        api_key = self.api_key_edit.text().strip()
        return api_key if api_key else None

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

    def generate_main_keywords(self):
        """SEO 메인 키워드 자동 생성"""
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "경고", "주제를 먼저 입력해주세요.")
            return

        # UI 업데이트
        self.main_keyword_btn.setEnabled(False)
        self.main_keyword_btn.setText("생성 중...")

        # 백그라운드 스레드에서 생성
        api_key = self.get_api_key()
        model = self.model_combo.currentText().strip()
        self.keyword_thread = KeywordGeneratorThread(topic=topic, api_key=api_key, model=model)
        self.keyword_thread.progress.connect(self.on_keyword_progress)
        self.keyword_thread.finished.connect(self.on_main_keywords_finished)
        self.keyword_thread.error.connect(self.on_keyword_error)
        self.keyword_thread.start()

    def generate_sub_keywords(self):
        """SEO 서브 키워드 자동 생성"""
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "경고", "주제를 먼저 입력해주세요.")
            return

        # UI 업데이트
        self.sub_keyword_btn.setEnabled(False)
        self.sub_keyword_btn.setText("생성 중...")

        # 백그라운드 스레드에서 생성
        api_key = self.get_api_key()
        model = self.model_combo.currentText().strip()
        self.keyword_thread = KeywordGeneratorThread(topic=topic, api_key=api_key, model=model)
        self.keyword_thread.progress.connect(self.on_keyword_progress)
        self.keyword_thread.finished.connect(self.on_sub_keywords_finished)
        self.keyword_thread.error.connect(self.on_keyword_error)
        self.keyword_thread.start()

    def on_keyword_progress(self, message: str):
        """키워드 생성 진행 상황 업데이트"""
        logger.info(message)

    def on_main_keywords_finished(self, result: dict):
        """메인 키워드 생성 완료 처리"""
        self.main_keyword_btn.setEnabled(True)
        self.main_keyword_btn.setText("자동 생성")

        main_keywords = result.get("main_keywords", [])
        if len(main_keywords) >= 1:
            self.main_keyword1_edit.setText(main_keywords[0])
        if len(main_keywords) >= 2:
            self.main_keyword2_edit.setText(main_keywords[1])

        QMessageBox.information(self, "완료", "SEO 메인 키워드가 생성되었습니다!")

    def on_sub_keywords_finished(self, result: dict):
        """서브 키워드 생성 완료 처리"""
        self.sub_keyword_btn.setEnabled(True)
        self.sub_keyword_btn.setText("자동 생성")

        sub_keywords = result.get("sub_keywords", [])
        if len(sub_keywords) >= 1:
            self.sub_keyword1_edit.setText(sub_keywords[0])
        if len(sub_keywords) >= 2:
            self.sub_keyword2_edit.setText(sub_keywords[1])
        if len(sub_keywords) >= 3:
            self.sub_keyword3_edit.setText(sub_keywords[2])

        QMessageBox.information(self, "완료", "SEO 서브 키워드가 생성되었습니다!")

    def on_keyword_error(self, error_message: str):
        """키워드 생성 오류 처리"""
        self.main_keyword_btn.setEnabled(True)
        self.main_keyword_btn.setText("자동 생성")
        self.sub_keyword_btn.setEnabled(True)
        self.sub_keyword_btn.setText("자동 생성")
        QMessageBox.critical(self, "오류", f"키워드 생성 중 오류가 발생했습니다:\n\n{error_message}")

    def generate_blog_post(self):
        """블로그 글 생성 시작"""
        # 입력 검증
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "경고", "주제를 입력해주세요.")
            return

        main_keyword1 = self.main_keyword1_edit.text().strip()
        if not main_keyword1:
            QMessageBox.warning(self, "경고", "SEO 메인 키워드를 최소 1개 입력해주세요.")
            return

        sub_keyword1 = self.sub_keyword1_edit.text().strip()
        sub_keyword2 = self.sub_keyword2_edit.text().strip()
        if not sub_keyword1 or not sub_keyword2:
            QMessageBox.warning(self, "경고", "SEO 서브 키워드를 최소 2개 입력해주세요.")
            return

        # 키워드 수집
        main_keywords = [main_keyword1]
        main_keyword2 = self.main_keyword2_edit.text().strip()
        if main_keyword2:
            main_keywords.append(main_keyword2)

        sub_keywords = [sub_keyword1, sub_keyword2]
        sub_keyword3 = self.sub_keyword3_edit.text().strip()
        if sub_keyword3:
            sub_keywords.append(sub_keyword3)

        tone = self.tone_combo.currentText()

        # UI 업데이트
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 무한 진행 표시
        self.markdown_edit.clear()
        self.seo_summary_edit.clear()
        self.review_points_edit.clear()

        # 백그라운드 스레드에서 생성
        api_key = self.get_api_key()
        model = self.model_combo.currentText().strip()
        self.generator_thread = BlogGeneratorThread(
            topic=topic,
            tone=tone,
            main_keywords=main_keywords,
            sub_keywords=sub_keywords,
            api_key=api_key,
            model=model,
        )
        self.generator_thread.progress.connect(self.on_progress)
        self.generator_thread.finished.connect(self.on_generation_finished)
        self.generator_thread.error.connect(self.on_generation_error)
        self.generator_thread.start()

    def on_progress(self, message: str):
        """진행 상황 업데이트"""
        logger.info(message)

    def on_generation_finished(self, result: dict):
        """생성 완료 처리"""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.publish_btn.setEnabled(True)

        # 결과 표시
        self.markdown_edit.setPlainText(result.get("markdown", ""))
        self.seo_summary_edit.setPlainText(result.get("seo_summary", ""))
        review_points = result.get("review_points", [])
        review_text = "\n".join(f"• {point}" for point in review_points)
        self.review_points_edit.setPlainText(review_text)

        QMessageBox.information(self, "완료", "블로그 글이 생성되었습니다!")

    def on_generation_error(self, error_message: str):
        """생성 오류 처리"""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "오류", f"블로그 글 생성 중 오류가 발생했습니다:\n\n{error_message}")

    def save_markdown(self):
        """마크다운 파일로 저장"""
        markdown_content = self.markdown_edit.toPlainText()
        if not markdown_content:
            QMessageBox.warning(self, "경고", "저장할 내용이 없습니다.")
            return

        # 파일 저장 대화상자
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "마크다운 파일 저장",
            "",
            "Markdown Files (*.md);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                QMessageBox.information(self, "성공", f"파일이 저장되었습니다:\n{file_path}")
            except Exception as e:
                logger.exception("파일 저장 실패")
                QMessageBox.critical(self, "오류", f"파일 저장 중 오류가 발생했습니다:\n\n{str(e)}")

    def publish_to_blog(self):
        """생성된 마크다운을 블로그에 발행"""
        markdown_content = self.markdown_edit.toPlainText()
        if not markdown_content:
            QMessageBox.warning(self, "경고", "발행할 내용이 없습니다.")
            return

        # 제목 추출 (마크다운의 첫 번째 헤더)
        title = None
        lines = markdown_content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break

        if not title:
            # 제목 입력 다이얼로그
            from PySide6.QtWidgets import QInputDialog
            title, ok = QInputDialog.getText(self, "제목 입력", "제목을 입력해주세요:")
            if not ok or not title:
                QMessageBox.warning(self, "경고", "제목이 필요합니다.")
                return

        # 임시 파일로 저장
        import tempfile
        import os
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"blog_post_{os.getpid()}.md")
        
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)
        except Exception as e:
            logger.exception("임시 파일 저장 실패")
            QMessageBox.critical(self, "오류", f"임시 파일 저장 중 오류가 발생했습니다:\n\n{str(e)}")
            return

        # 발행 옵션 수집
        blog_id = self.blog_id_edit.text().strip() or get_blogid()
        if not blog_id:
            QMessageBox.warning(self, "경고", "Blog ID를 설정해주세요.")
            return

        is_draft = self.draft_checkbox.isChecked()

        # 발행 시점 설정
        publish_time_text = self.publish_time_combo.currentText()
        publish_time_hour = self.publish_time_hour_spin.value()
        
        datetime_string = None
        if publish_time_hour > 0:
            datetime_string = get_datetime_after_hour(publish_time_hour)
        else:
            time_map = {
                "즉시": "now",
                "1분 후": "1m",
                "10분 후": "10m",
                "1시간 후": "1h",
                "1일 후": "1d",
                "1주 후": "1w",
                "1개월 후": "1M",
            }
            after_string = time_map.get(publish_time_text, "now")
            datetime_string = get_datetime_after(after_string)

        # 라벨 처리
        labels = None
        labels_text = self.labels_edit.text().strip()
        if labels_text:
            labels = [label.strip() for label in labels_text.split(",") if label.strip()]

        # 설명 처리
        description = self.description_edit.text().strip() or None

        # 썸네일 처리
        thumbnail = self.thumbnail_edit.text().strip() or None

        # 발행 실행
        try:
            self.publish_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            post_info = upload_to_blogspot(
                title=title,
                fn=temp_file,
                BLOG_ID=blog_id,
                is_draft=is_draft,
                datetime_string=datetime_string,
                labels=labels,
                search_description=description,
                thumbnail=thumbnail,
            )

            self.progress_bar.setVisible(False)
            self.publish_btn.setEnabled(True)

            status = "드래프트로 저장" if is_draft else "발행"
            QMessageBox.information(
                self,
                "발행 완료",
                f"게시물이 성공적으로 {status}되었습니다.\n\n"
                f"Post ID: {post_info['id']}\n"
                f"URL: {post_info['url']}",
            )
        except Exception as e:
            logger.exception("블로그 발행 실패")
            self.progress_bar.setVisible(False)
            self.publish_btn.setEnabled(True)
            QMessageBox.critical(self, "오류", f"블로그 발행 중 오류가 발생했습니다:\n\n{str(e)}")
        finally:
            # 임시 파일 삭제
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {e}")

    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        threads_running = False
        if self.generator_thread and self.generator_thread.isRunning():
            threads_running = True
        if self.keyword_thread and self.keyword_thread.isRunning():
            threads_running = True

        if threads_running:
            reply = QMessageBox.question(
                self,
                "확인",
                "작업이 진행 중입니다. 정말 닫으시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                if self.generator_thread and self.generator_thread.isRunning():
                    self.generator_thread.terminate()
                    self.generator_thread.wait()
                if self.keyword_thread and self.keyword_thread.isRunning():
                    self.keyword_thread.terminate()
                    self.keyword_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

