import sys
import asyncio
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QLabel, QPushButton, QListWidget,
    QGroupBox, QLineEdit, QRadioButton, QProgressBar,
    QListWidgetItem, QMessageBox, QFileDialog,
    QSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction
from loguru import logger

from .database import init_db, close_db
from .models import Workspace, PublishRecord
from .views.workspace_dialog import WorkspaceDialog
from .views.publish_records_dialog import PublishRecordsDialog
from .views.settings_dialog import SettingsDialog
from .views.blog_generator_dialog import BlogGeneratorDialog
from .utils.publisher import PublisherThread, SchedulerThread, ConverterThread

# Import for convert functionality
try:
    from markdown_to_blog.libs.markdown import upload_markdown_images
except ImportError:
    # Fallback to relative import
    from ...libs.markdown import upload_markdown_images


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_workspace = None
        self.publisher_thread = None
        self.scheduler_thread = None
        self.converter_thread = None
        self.init_ui()
        self.setup_async()
        
    def init_ui(self):
        self.setWindowTitle("Markdown to Blog GUI")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Workspace list
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Workspace details and publish management
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 700])
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("파일")
        
        new_workspace_action = QAction("새 워크스페이스", self)
        new_workspace_action.triggered.connect(self.new_workspace)
        file_menu.addAction(new_workspace_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("도구")
        
        blog_generator_action = QAction("블로그 글 자동 생성", self)
        blog_generator_action.triggered.connect(self.open_blog_generator)
        tools_menu.addAction(blog_generator_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("설정")
        
        global_settings_action = QAction("전역 설정", self)
        global_settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(global_settings_action)
        
    def create_left_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("워크스페이스 목록")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title)
        
        # New workspace button
        new_btn = QPushButton("+ 새 워크스페이스")
        new_btn.clicked.connect(self.new_workspace)
        layout.addWidget(new_btn)
        
        # Workspace list
        self.workspace_list = QListWidget()
        self.workspace_list.itemClicked.connect(self.on_workspace_selected)
        layout.addWidget(self.workspace_list)
        
        return widget
        
    def create_right_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Workspace details
        details_group = QGroupBox("워크스페이스 상세")
        details_layout = QFormLayout()
        
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setReadOnly(True)
        folder_btn = QPushButton("폴더 선택")
        folder_btn.clicked.connect(self.select_folder)
        
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_path_edit)
        folder_layout.addWidget(folder_btn)
        
        self.blog_id_edit = QLineEdit()
        
        # Publish interval radio buttons
        interval_layout = QHBoxLayout()
        self.daily_radio = QRadioButton("매일")
        self.weekly_radio = QRadioButton("매주")
        self.custom_radio = QRadioButton("사용자 정의")
        self.custom_interval = QSpinBox()
        self.custom_interval.setMinimum(1)
        self.custom_interval.setMaximum(999)
        self.custom_interval.setSuffix(" 시간")
        self.custom_interval.setEnabled(False)
        
        self.custom_radio.toggled.connect(lambda checked: self.custom_interval.setEnabled(checked))
        
        interval_layout.addWidget(self.daily_radio)
        interval_layout.addWidget(self.weekly_radio)
        interval_layout.addWidget(self.custom_radio)
        interval_layout.addWidget(self.custom_interval)
        interval_layout.addStretch()
        
        details_layout.addRow("폴더 경로:", folder_layout)
        details_layout.addRow("Blog ID:", self.blog_id_edit)
        details_layout.addRow("발행 주기:", interval_layout)
        
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save_workspace_settings)
        details_layout.addRow("", save_btn)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Publish management
        publish_group = QGroupBox("발행 관리")
        publish_layout = QVBoxLayout()
        
        button_layout = QHBoxLayout()
        
        self.schedule_btn = QPushButton("스케줄")
        self.schedule_btn.clicked.connect(self.start_scheduling)
        button_layout.addWidget(self.schedule_btn)
        
        self.convert_btn = QPushButton("변환")
        self.convert_btn.clicked.connect(self.start_converting)
        button_layout.addWidget(self.convert_btn)
        
        self.start_btn = QPushButton("발행 시작")
        self.start_btn.clicked.connect(self.start_publishing)
        self.stop_btn = QPushButton("발행 중지")
        self.stop_btn.clicked.connect(self.stop_publishing)
        self.stop_btn.setEnabled(False)
        self.records_btn = QPushButton("기록 보기")
        self.records_btn.clicked.connect(self.show_records)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.records_btn)
        
        publish_layout.addLayout(button_layout)
        
        # Progress
        self.progress_label = QLabel("대기 중...")
        publish_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        publish_layout.addWidget(self.progress_bar)
        
        publish_group.setLayout(publish_layout)
        layout.addWidget(publish_group)
        
        layout.addStretch()
        
        return widget
        
    def setup_async(self):
        """Setup async event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Initialize database
        self.loop.run_until_complete(init_db())
        
        # Load workspaces
        self.load_workspaces()
        
    def load_workspaces(self):
        """Load workspaces from database"""
        async def _load():
            workspaces = await Workspace.all()
            return workspaces
            
        workspaces = self.loop.run_until_complete(_load())
        
        self.workspace_list.clear()
        for workspace in workspaces:
            item = QListWidgetItem(workspace.name)
            item.setData(Qt.UserRole, workspace.id)
            self.workspace_list.addItem(item)
            
    def new_workspace(self):
        """Create new workspace"""
        dialog = WorkspaceDialog(self)
        if dialog.exec():
            name = dialog.name_edit.text()
            
            async def _create():
                workspace = await Workspace.create(name=name, folder_path="")
                return workspace
                
            workspace = self.loop.run_until_complete(_create())
            
            # Add to list
            item = QListWidgetItem(workspace.name)
            item.setData(Qt.UserRole, workspace.id)
            self.workspace_list.addItem(item)
            
            # Select it
            self.workspace_list.setCurrentItem(item)
            self.on_workspace_selected(item)
            
    def on_workspace_selected(self, item):
        """Handle workspace selection"""
        workspace_id = item.data(Qt.UserRole)
        
        async def _load():
            workspace = await Workspace.get(id=workspace_id)
            return workspace
            
        self.current_workspace = self.loop.run_until_complete(_load())
        
        # Update UI
        self.folder_path_edit.setText(self.current_workspace.folder_path or "")
        self.blog_id_edit.setText(self.current_workspace.blog_id or "")
        
        # Set publish interval
        interval = self.current_workspace.publish_interval
        if interval == "daily":
            self.daily_radio.setChecked(True)
        elif interval == "weekly":
            self.weekly_radio.setChecked(True)
        elif interval and interval.startswith("custom:"):
            self.custom_radio.setChecked(True)
            hours = int(interval.split(":")[1])
            self.custom_interval.setValue(hours)
        else:
            self.daily_radio.setChecked(True)
            
    def select_folder(self):
        """Select folder for workspace"""
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            self.folder_path_edit.setText(folder)
            
    def save_workspace_settings(self):
        """Save workspace settings"""
        if not self.current_workspace:
            QMessageBox.warning(self, "경고", "워크스페이스를 선택해주세요.")
            return
            
        # Get publish interval
        if self.daily_radio.isChecked():
            interval = "daily"
        elif self.weekly_radio.isChecked():
            interval = "weekly"
        elif self.custom_radio.isChecked():
            interval = f"custom:{self.custom_interval.value()}"
        else:
            interval = "daily"
            
        async def _update():
            self.current_workspace.folder_path = self.folder_path_edit.text()
            self.current_workspace.blog_id = self.blog_id_edit.text()
            self.current_workspace.publish_interval = interval
            await self.current_workspace.save()
            
        self.loop.run_until_complete(_update())
        
        QMessageBox.information(self, "성공", "설정이 저장되었습니다.")
        
    def start_scheduling(self):
        """Start scheduling process"""
        if not self.current_workspace:
            QMessageBox.warning(self, "경고", "워크스페이스를 선택해주세요.")
            return
            
        if not self.current_workspace.folder_path or not self.current_workspace.blog_id:
            QMessageBox.warning(self, "경고", "폴더 경로와 Blog ID를 설정해주세요.")
            return
            
        self.schedule_btn.setEnabled(False)
        
        # Create and start scheduler thread
        self.scheduler_thread = SchedulerThread(
            self.current_workspace,
            self.loop
        )
        self.scheduler_thread.progress.connect(self.update_progress)
        self.scheduler_thread.finished.connect(self.on_scheduling_finished)
        self.scheduler_thread.start()
    
    def start_converting(self):
        """Start converting markdown images"""
        if not self.current_workspace:
            QMessageBox.warning(self, "경고", "워크스페이스를 선택해주세요.")
            return
            
        if not self.current_workspace.folder_path:
            QMessageBox.warning(self, "경고", "폴더 경로를 설정해주세요.")
            return
        
        self.convert_btn.setEnabled(False)
        
        # Create and start converter thread
        self.converter_thread = ConverterThread(
            self.current_workspace,
            self.loop
        )
        self.converter_thread.progress.connect(self.update_progress)
        self.converter_thread.finished.connect(self.on_converting_finished)
        self.converter_thread.start()
    
    def start_publishing(self):
        """Start publishing process"""
        if not self.current_workspace:
            QMessageBox.warning(self, "경고", "워크스페이스를 선택해주세요.")
            return
            
        if not self.current_workspace.folder_path or not self.current_workspace.blog_id:
            QMessageBox.warning(self, "경고", "폴더 경로와 Blog ID를 설정해주세요.")
            return
            
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Create and start publisher thread
        self.publisher_thread = PublisherThread(
            self.current_workspace,
            self.loop
        )
        self.publisher_thread.progress.connect(self.update_progress)
        self.publisher_thread.finished.connect(self.on_publishing_finished)
        self.publisher_thread.start()
        
    def stop_publishing(self):
        """Stop publishing process"""
        if self.publisher_thread:
            self.publisher_thread.stop()
            
    @Slot(str, int, int)
    def update_progress(self, message, current, total):
        """Update progress"""
        self.progress_label.setText(message)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
    @Slot()
    def on_scheduling_finished(self):
        """Handle scheduling finished"""
        self.schedule_btn.setEnabled(True)
        self.progress_label.setText("스케줄 완료")
    
    @Slot()
    def on_publishing_finished(self):
        """Handle publishing finished"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("발행 완료")
    
    @Slot()
    def on_scheduling_finished(self):
        """Handle scheduling finished"""
        self.schedule_btn.setEnabled(True)
        self.progress_label.setText("스케줄 완료")
    
    @Slot()
    def on_converting_finished(self):
        """Handle converting finished"""
        self.convert_btn.setEnabled(True)
        self.progress_label.setText("변환 완료")
        
    def show_records(self):
        """Show publish records"""
        if not self.current_workspace:
            QMessageBox.warning(self, "경고", "워크스페이스를 선택해주세요.")
            return
            
        dialog = PublishRecordsDialog(self.current_workspace, self.loop, self)
        dialog.exec()
        
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.loop, self)
        dialog.exec()
    
    def open_blog_generator(self):
        """Open blog generator dialog (modeless)"""
        dialog = BlogGeneratorDialog(self)
        dialog.show()  # 모달리스이므로 show() 사용
        
    def closeEvent(self, event):
        """Handle close event"""
        # Stop publisher thread if running
        if self.publisher_thread and self.publisher_thread.isRunning():
            self.publisher_thread.stop()
            self.publisher_thread.wait()
            
        # Close database
        self.loop.run_until_complete(close_db())
        
        event.accept()