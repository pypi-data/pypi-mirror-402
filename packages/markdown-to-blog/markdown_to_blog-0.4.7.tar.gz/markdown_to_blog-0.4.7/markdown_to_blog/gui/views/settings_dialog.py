from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QPushButton,
    QFileDialog, QDialogButtonBox,
    QGroupBox, QHBoxLayout
)

from ..models import Setting


class SettingsDialog(QDialog):
    def __init__(self, loop, parent=None):
        super().__init__(parent)
        self.loop = loop
        self.setWindowTitle("전역 설정")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # API Settings
        api_group = QGroupBox("API 설정")
        api_layout = QFormLayout()
        
        secret_layout = QHBoxLayout()
        self.secret_file_edit = QLineEdit()
        browse_btn = QPushButton("찾아보기")
        browse_btn.clicked.connect(self.browse_secret_file)
        secret_layout.addWidget(self.secret_file_edit)
        secret_layout.addWidget(browse_btn)
        
        api_layout.addRow("Client Secret 파일:", secret_layout)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Publish Settings
        publish_group = QGroupBox("발행 설정")
        publish_layout = QFormLayout()
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(100)
        self.batch_size_spin.setValue(30)
        self.batch_size_spin.setSuffix(" 개")
        
        self.wait_time_spin = QSpinBox()
        self.wait_time_spin.setMinimum(1)
        self.wait_time_spin.setMaximum(300)
        self.wait_time_spin.setValue(60)
        self.wait_time_spin.setSuffix(" 초")
        
        publish_layout.addRow("배치 크기:", self.batch_size_spin)
        publish_layout.addRow("대기 시간:", self.wait_time_spin)
        publish_group.setLayout(publish_layout)
        layout.addWidget(publish_group)
        
        # Database Settings
        db_group = QGroupBox("데이터베이스")
        db_layout = QFormLayout()
        
        db_path_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        db_browse_btn = QPushButton("찾아보기")
        db_browse_btn.clicked.connect(self.browse_db_path)
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(db_browse_btn)
        
        db_layout.addRow("DB 경로:", db_path_layout)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            parent=self
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def browse_secret_file(self):
        """Browse for client secret file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Client Secret 파일 선택", "", "JSON Files (*.json)"
        )
        if file_path:
            self.secret_file_edit.setText(file_path)
            
    def browse_db_path(self):
        """Browse for database path"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "데이터베이스 파일 선택", "", "SQLite Database (*.db)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
            
    def load_settings(self):
        """Load settings from database"""
        async def _load():
            settings = {}
            all_settings = await Setting.all()
            for setting in all_settings:
                settings[setting.key] = setting.value
            return settings
            
        settings = self.loop.run_until_complete(_load())
        
        # Load values
        self.secret_file_edit.setText(settings.get("client_secret_file", ""))
        self.batch_size_spin.setValue(int(settings.get("batch_size", "30")))
        self.wait_time_spin.setValue(int(settings.get("wait_time", "60")))
        
        # DB path is read-only, just show current path
        from ..database import get_db_path
        self.db_path_edit.setText(get_db_path())
        
    def save_settings(self):
        """Save settings to database"""
        async def _save():
            # Save client secret file
            await Setting.update_or_create(
                key="client_secret_file",
                defaults={"value": self.secret_file_edit.text()}
            )
            
            # Save batch size
            await Setting.update_or_create(
                key="batch_size",
                defaults={"value": str(self.batch_size_spin.value())}
            )
            
            # Save wait time
            await Setting.update_or_create(
                key="wait_time",
                defaults={"value": str(self.wait_time_spin.value())}
            )
            
        self.loop.run_until_complete(_save())
        self.accept()