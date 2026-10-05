from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from gui.pages.chat_widget import ChatWidget
from gui.pages.quiz_widget import QuizWidget
from gui.pages.teach_widget import TeachWidget
from gui.pages.history_widget import HistoryWidget
from gui.pages.settings_widget import SettingsWidget
from core.database import Database
from models.user import User

class MainWindow(QMainWindow):
    def __init__(self, user: User):
        super().__init__()
        self.db = Database()
        self.user = user

        self.setWindowTitle("EduMentor - AI Teaching Assistant")
        self.setGeometry(300, 60, 1000, 700)

        self.chat_widget = ChatWidget(self.db, self.user.user_id)
        self.quiz_widget = QuizWidget(self.db)
        self.teach_widget = TeachWidget(self.db)
        self.history_widget = HistoryWidget(self.db, self.user.user_id)
        self.settings_widget = SettingsWidget(self.db, self.user)

        self.history_widget.refresh_history()
        self.history_widget.session_load_requested.connect(self.on_session_load_requested)
        self.history_widget.session_delete_requested.connect(self.on_session_delete_requested)
        self.chat_widget.session_load_requested.connect(self.on_session_load_requested)
        self.settings_widget.logout_requested.connect(self.close)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.chat_widget, '📖 Mentor')
        self.tabs.addTab(self.quiz_widget, '📝 Quiz')
        self.tabs.addTab(self.teach_widget, '🗣️ Teach-back')
        self.tabs.addTab(self.history_widget, '📚 History')
        self.tabs.addTab(self.settings_widget, '⚙️ Settings')
        self.setCentralWidget(self.tabs)

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_session_load_requested(self, session_obj, tab_idx, item_idx, flag):
        if flag:
            self.history_widget.refresh_history()
        
        self.chat_widget.load_session(session_obj, flag)
        self.quiz_widget.load_session(session_obj, item_idx)
        self.teach_widget.load_session(session_obj, item_idx)
        self.tabs.setCurrentIndex(tab_idx)

    def on_session_delete_requested(self):
        self.chat_widget.create_new_chat(True)
        self.quiz_widget.current_session = None
        self.quiz_widget.create_new_quiz(True)
        self.teach_widget.current_session = None
        self.teach_widget.create_new_teachback(True)
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(0)
        self.tabs.blockSignals(False)

    def on_tab_changed(self, index):
        if index == 1:
            self.quiz_widget.check_if_valid()
        elif index ==2:
            self.teach_widget.check_if_valid()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Log-out',
                                    'Are you sure you want to logout?',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            event.ignore()
            return
        
        self.chat_widget.save_chat_session(silent=True)
        self.quiz_widget.save_quiz_session(silent=True)
        self.teach_widget.save_teachback_session(silent=True)
        event.accept()