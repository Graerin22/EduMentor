import sys
import qdarktheme
from PyQt6.QtWidgets import QApplication
from gui.main.main_window import MainWindow
from gui.main.login_window import LoginWindow
from models.user import User

class EduMentor:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(qdarktheme.load_stylesheet('dark'))
        self.login_window = None
        self.main_window = None

    def _show_login(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.login_window = LoginWindow()
        self.login_window.login_widget.login_successful.connect(self.on_login)
        self.login_window.show()
    
    def run(self):
        self._show_login()
        sys.exit(self.app.exec())

    def on_login(self, user: User):
        self.main_window = MainWindow(user)
        self.main_window.login_requested.connect(self._show_login)
        self.main_window.show()

if __name__ == '__main__':
    EduMentor().run()