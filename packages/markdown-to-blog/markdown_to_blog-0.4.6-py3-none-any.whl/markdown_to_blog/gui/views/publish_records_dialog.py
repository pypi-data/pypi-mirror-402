from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from datetime import datetime
from pathlib import Path
from loguru import logger

from ...libs.blogger import upload_to_blogspot
from ...libs.markdown import read_first_header_from_md

from ..models import PublishRecord


class PublishRecordsDialog(QDialog):
    def __init__(self, workspace, loop, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.loop = loop
        self.setWindowTitle(f"발행 기록 - {workspace.name}")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.load_records()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_records)
        search_layout.addWidget(self.search_edit)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_records)
        search_layout.addWidget(refresh_btn)
        
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["파일명", "예약 시간", "발행 시간", "Blog ID", "상태", "Post ID", "URL"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        retry_btn = QPushButton("재발행")
        retry_btn.clicked.connect(self.retry_publish)
        button_layout.addWidget(retry_btn)
        
        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_record)
        button_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("내보내기")
        export_btn.clicked.connect(self.export_records)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def load_records(self):
        """Load publish records"""
        async def _load():
            records = await PublishRecord.filter(workspace=self.workspace).all()
            return records
            
        records = self.loop.run_until_complete(_load())
        self._records = records
        
        self.table.setRowCount(len(records))
        for i, record in enumerate(records):
            # Filename
            self.table.setItem(i, 0, QTableWidgetItem(record.filename))
            
            # Scheduled time
            scheduled_str = record.scheduled.strftime("%Y-%m-%d %H:%M") if record.scheduled else ""
            self.table.setItem(i, 1, QTableWidgetItem(scheduled_str))
            
            # Published time
            published_str = record.published_at.strftime("%Y-%m-%d %H:%M") if record.published_at else ""
            self.table.setItem(i, 2, QTableWidgetItem(published_str))
            
            # Blog ID
            self.table.setItem(i, 3, QTableWidgetItem(record.blog_id or ""))
            
            # Status
            status_item = QTableWidgetItem(record.status)
            if record.status == "published":
                status_item.setBackground(Qt.green)
            elif record.status == "failed":
                status_item.setBackground(Qt.red)
            elif record.status == "scheduled":
                status_item.setBackground(Qt.yellow)
            elif record.status == "publishing":
                status_item.setBackground(Qt.cyan)
            self.table.setItem(i, 4, status_item)
            
            # Post ID
            self.table.setItem(i, 5, QTableWidgetItem(record.post_id or ""))
            
            # URL
            url_item = QTableWidgetItem(record.post_url or "")
            if record.post_url:
                url_item.setToolTip(record.post_url)
            self.table.setItem(i, 6, url_item)
            
        self.table.resizeColumnsToContents()
        
    def filter_records(self, text):
        """Filter records by search text"""
        for i in range(self.table.rowCount()):
            hidden = True
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and text.lower() in item.text().lower():
                    hidden = False
                    break
            self.table.setRowHidden(i, hidden)
            
    def retry_publish(self):
        """Retry publishing for selected records"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.warning(self, "경고", "재발행할 항목을 선택해주세요.")
            return

        success = 0
        failed = 0
        for row in sorted(selected_rows):
            try:
                record = self._records[row]
                # 결정: 파일 경로 해석 (절대경로 아니면 워크스페이스 폴더 기준)
                file_path = Path(record.filename)
                if not file_path.is_absolute():
                    base = Path(self.workspace.folder_path) if self.workspace and self.workspace.folder_path else Path.cwd()
                    file_path = (base / record.filename).resolve()

                if not file_path.exists():
                    logger.error(f"파일을 찾을 수 없습니다: {file_path}")
                    failed += 1
                    self._update_record_sync(record, status="failed", error_message=f"파일 없음: {file_path}")
                    continue

                # 제목 추출 (없으면 파일명 사용)
                title = read_first_header_from_md(str(file_path)) or file_path.stem

                blog_id = record.blog_id or getattr(self.workspace, "blog_id", None)
                if not blog_id:
                    failed += 1
                    self._update_record_sync(record, status="failed", error_message="Blog ID 미설정")
                    continue

                # 상태 업데이트: publishing
                self._update_record_sync(record, status="publishing", error_message=None)

                # 즉시 발행 (예약 없음)
                result = upload_to_blogspot(
                    title=title,
                    fn=str(file_path),
                    BLOG_ID=blog_id,
                    is_draft=False,
                    datetime_string=None,
                    labels=None,
                    search_description=None,
                    thumbnail=None,
                )

                # 성공 업데이트
                record.post_id = result.get("id")
                record.post_url = result.get("url")
                record.published_at = datetime.now()
                record.blog_id = blog_id
                self._update_record_sync(record, status="published", error_message=None)
                success += 1
            except Exception as e:
                logger.exception("재발행 실패")
                self._update_record_sync(record, status="failed", error_message=str(e))
                failed += 1

        self.load_records()
        QMessageBox.information(self, "재발행 결과", f"성공 {success}건, 실패 {failed}건")

    def _update_record_sync(self, record: PublishRecord, status: str, error_message: str | None):
        async def _update():
            record.status = status
            record.error_message = error_message
            await record.save()
        self.loop.run_until_complete(_update())
        
    def delete_record(self):
        """Delete selected records"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.warning(self, "경고", "삭제할 항목을 선택해주세요.")
            return
            
        reply = QMessageBox.question(
            self, "확인", 
            f"{len(selected_rows)}개의 기록을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: Implement delete logic
            QMessageBox.information(self, "정보", "삭제 기능은 아직 구현되지 않았습니다.")
            
    def export_records(self):
        """Export records to file"""
        # TODO: Implement export logic
        QMessageBox.information(self, "정보", "내보내기 기능은 아직 구현되지 않았습니다.")