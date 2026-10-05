import os
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from utils.sliding_stack import SlidingStackedWidget
from core.ai_engine import AIWorker
from core.database import Database

CURR_DIR = Path(__file__).resolve().parents[2]
UI1_FILE_PATH = CURR_DIR / 'ui_designs' / 'register_widget1.ui'
UI2_FILE_PATH = CURR_DIR / 'ui_designs' / 'register_widget2.ui'

class RegisterWidget(SlidingStackedWidget):
    def __init__(self, login_window, db: Database):
        super().__init__()
        self.login_window = login_window
        self.db = db

        register1 = QWidget()
        uic.loadUi(str(UI1_FILE_PATH), register1)
        register2 = QWidget()
        uic.loadUi(str(UI2_FILE_PATH), register2)
        self.addWidget(register1)
        self.addWidget(register2)

        self.step1_register = self.widget(0)
        self.step1_register.view_pass_btn.clicked.connect(self._view_unview_password)
        self.step1_register.view_confpass_btn.clicked.connect(self._view_unview_confirm_password)
        self.step1_register.next_btn.clicked.connect(self._go_to_step2)
        self.step1_register.login_btn.clicked.connect(lambda: self.login_window.tabs.setCurrentIndex(0))

        self.step2_register = self.widget(1)
        self.step2_register.open_link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://aistudio.google.com')))
        self.step2_register.models_combobox.currentTextChanged.connect(self.on_selection_changed)
        self.step2_register.back_btn.clicked.connect(lambda: self.slide_to_index(0))
        self.step2_register.test_btn.clicked.connect(self._test_key)
        self.step2_register.finish_btn.clicked.connect(self._finish_registration)

    def _go_to_step2(self):
        username = self.step1_register.reg_username.text().strip()
        password = self.step1_register.reg_password.text()
        confirm = self.step1_register.reg_confpass.text()

        if not username or not password:
            QMessageBox.warning(self, 'Missing info', 'All fields are required.')
            return
        if len(password) < 6:
            QMessageBox.warning(self, 'Weak password', 'Use at least 6 characters.')
            return
        if password != confirm:
            QMessageBox.warning(self, 'Mismatch', 'Passwords do not match.')
            return
        
        self.pending_username = username
        self.pending_password = password
        self.slide_to_index(1)

    def _view_unview_password(self):
        if self.step1_register.reg_password.echoMode() == QLineEdit.EchoMode.Password:
            self.step1_register.reg_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.step1_register.reg_password.setEchoMode(QLineEdit.EchoMode.Password)

    def _view_unview_confirm_password(self):
        if self.step1_register.reg_confpass.echoMode() == QLineEdit.EchoMode.Password:
            self.step1_register.reg_confpass.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.step1_register.reg_confpass.setEchoMode(QLineEdit.EchoMode.Password)

    def on_selection_changed(self, selected_text):
        os.environ['GEMINI_MODEL'] = selected_text

    def _test_key(self):
        api_key = self.step2_register.api_key_input.text().strip()
        if not api_key:
            self.step2_register.key_status_label.setText('❌ Please enter a key first.')
            return

        self.step2_register.key_status_label.setText('⌛ Testing your key...')
        self.step2_register.api_key_input.setEnabled(False)
        self.step2_register.test_btn.setEnabled(False)

        os.environ['GEMINI_API_KEY'] = api_key
        os.environ['GEMINI_MODEL'] = self.step2_register.models_combobox.currentText()
        content = [{'role':'user', 'parts':'ping'}]
        self.ai_worker = AIWorker(content)
        self.ai_worker.finished.connect(self._handle_valid_key)
        self.ai_worker.error.connect(self._handle_invalid_key)
        self.ai_worker.start()

    def _handle_valid_key(self, _):
        self.step2_register.key_status_label.setText('✅ Key is valid! You can now finish setup.')
        self.step2_register.api_key_input.setEnabled(True)
        self.step2_register.finish_btn.setEnabled(True)

    def _handle_invalid_key(self, error_msg):
        if '503 UNAVAILABLE' in error_msg:
            self.step2_register.key_status_label.setText('⚠️ Google servers overloaded.')
        else:
            self.step2_register.key_status_label.setText('❌ Invalid key!')

        self.step2_register.api_key_input.clear()
        self.step2_register.api_key_input.setEnabled(True)
        self.step2_register.test_btn.setEnabled(True)

    def _finish_registration(self):
        api_key = self.step2_register.api_key_input.text().strip()
        success, message = self.db.register_user(self.pending_username,
                                                 self.pending_password,
                                                 api_key)
        if success:
            QMessageBox.information(self, 'Success', 'Account created! You can now log in.')
            self.login_window.login_widget.login_username.setText(self.pending_username)
            self.login_window.login_widget.login_password.setText(self.pending_password)
            self.login_window.tabs.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, 'Registration Failed', message)