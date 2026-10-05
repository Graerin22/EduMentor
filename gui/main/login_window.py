from PyQt6.QtWidgets import QMainWindow, QTabWidget
from gui.pages.login_widget import LoginWidget
from gui.pages.register_widget import RegisterWidget
from core.database import Database

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()

        self.setWindowTitle('EduMentor')
        self.setFixedSize(460, 520)

        self.login_widget = LoginWidget(self, self.db)
        self.register_widget = RegisterWidget(self, self.db)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.login_widget, '👤 Login')
        self.tabs.addTab(self.register_widget, '📝 Register')
        self.setCentralWidget(self.tabs)