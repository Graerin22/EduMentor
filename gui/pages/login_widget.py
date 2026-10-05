from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit
from PyQt6.QtCore import pyqtSignal
from core.database import Database
from utils.config import set_model, set_api_key
from models.user import User

CURR_DIR = Path(__file__).resolve().parents[2]
UI_FILE_PATH = CURR_DIR / 'ui_designs' / 'login_widget.ui'

class LoginWidget(QWidget):
    login_successful = pyqtSignal(User)

    def __init__(self, login_window, db: Database):
        super().__init__()
        self.db = db
        self.login_window = login_window

        uic.loadUi(str(UI_FILE_PATH), self)

        self.view_pass_btn.clicked.connect(self._view_password)
        self.login_btn.clicked.connect(self._handle_login)
        self.signup_btn.clicked.connect(lambda: self.login_window.tabs.setCurrentIndex(1))
    
    def _handle_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Missing Info', 'Enter username and password.')
            return

        success, result = self.db.authenticate_user(username, password)
        if success:
            self.login_successful.emit(result)
            self.login_username.clear()
            self.login_password.clear()
            self.login_window.close()
        else:
            QMessageBox.warning(self, 'Login Failed', result)

    def _view_password(self):
        if self.login_password.echoMode() == QLineEdit.EchoMode.Password:
            self.login_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.login_password.setEchoMode(QLineEdit.EchoMode.Password)