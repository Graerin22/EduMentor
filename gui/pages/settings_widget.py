import os
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QLineEdit, QMessageBox, QInputDialog
from core.database import Database
from core.ai_engine import AIWorker
from utils.config import set_api_key, set_model
from models.user import User

CURR_DIR = Path(__file__).resolve().parents[2]
UI_FILE_PATH = CURR_DIR / 'ui_designs' / 'settings_widget.ui'

class SettingsWidget(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, db: Database, user: User):
        super().__init__()
        self.db = db
        self.user = user

        uic.loadUi(str(UI_FILE_PATH), self)

        self.username_display.setText(self.user.username)

        self.cng_username_btn.clicked.connect(self._change_username)
        self.cng_password_btn.clicked.connect(self._change_password)
        self.cng_api_btn.clicked.connect(self._change_api_key)
        self.test_btn.clicked.connect(self._test_key)
        self.models_combobox.currentTextChanged.connect(lambda x: set_model(x))
        self.delete_acc_btn.clicked.connect(self._delete_account)
        self.logout_btn.clicked.connect(lambda: self.logout_requested.emit())

    def _change_username(self):
        new_username, ok = QInputDialog.getText(self, 'Change username', 'Enter new username: ', text=self.user.username)
        if not ok or not new_username.strip():
            return

        success, message = self.db.change_username(new_username, self.user)
        if success:
            QMessageBox.information(self, 'Changed', f'Username changed to:\n{new_username}')
            self.username_display.setText(new_username)
        else:
            QMessageBox.warning(self, 'Change Failed', message)

    def _change_password(self):
        new_password, ok = QInputDialog.getText(self, 'Change password', 'Enter new password: ', echo=QLineEdit.EchoMode.Password)
        if not ok or not new_password:
            return

        confirm_password, ok = QInputDialog.getText(self, 'Confirm password', 'Enter confirm password: ', echo=QLineEdit.EchoMode.Password)
        if not ok:
            return
        if confirm_password == new_password:
            QMessageBox.information(self, 'Changed', 'Password is changed successfully.')
            success, message = self.db.change_password(new_password, self.user.user_id)
            if not success:
                QMessageBox.warning(self, 'Delete Failed', message)
        else:
            QMessageBox.warning(self, 'Change Failed', 'Please enter the same new and confirm password.')

    def _test_key(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.key_status_label.setText('❌ Please enter a key first.')
            return

        self.key_status_label.setText('⌛ Testing your key...')
        self.api_key_input.setEnabled(False)
        self.test_btn.setEnabled(False)

        os.environ['GEMINI_API_KEY'] = api_key
        content = [{'role':'user', 'parts':'ping'}]
        self.ai_worker = AIWorker(content)
        self.ai_worker.finished.connect(self._handle_valid_key)
        self.ai_worker.error.connect(self._handle_invalid_key)
        self.ai_worker.start()

    def _handle_valid_key(self, _):
        self.key_status_label.setText('✅ Key is valid! You can now update your API KEY.')
        self.api_key_input.setEnabled(True)
        self.test_btn.setEnabled(True)
        self.cng_api_btn.setEnabled(True)

    def _handle_invalid_key(self, error_msg):
        if '503 UNAVAILABLE' in error_msg:
            self.key_status_label.setText('⚠️ Google servers overloaded.\nYou can try changing the AI model')
        else:
            self.key_status_label.setText('❌ Invalid key!')

        self.api_key_input.clear()
        self.api_key_input.setEnabled(True)
        self.test_btn.setEnabled(True)

    def _change_api_key(self):
        api_key = self.api_key_input.text().strip()

        success, message = self.db.change_api_key(api_key, self.user)
        if success:
            set_api_key(api_key)
            QMessageBox.information(self, 'Changed', 'API key is changed successfully.')
        else:
            QMessageBox.warning(self, 'Change Failed', message)

        self.api_key_input.clear()
        self.cng_api_btn.setEnabled(False)

    def _delete_account(self):
        option = QMessageBox.warning(self, 'Delete account', 'Are you sure you want to delete this account?\nThis cannot be undone.',
                            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            defaultButton=QMessageBox.StandardButton.No)

        if option == QMessageBox.StandardButton.No:
            return

        success, message = self.db.delete_account(self.user)
        if success:
            QMessageBox.information(self, 'Deleted', 'Account deleted successfully.')
        else:
            QMessageBox.warning(self, 'Delete Failed', message)