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
    
    def run(self):
        self.login_window = LoginWindow()
        self.login_window.login_widget.login_successful.connect(self.on_login)
        self.login_window.show()
        sys.exit(self.app.exec())

    def on_login(self, user: User):
        self.main_window = MainWindow(user)
        self.main_window.login_requested.connect(self.run)
        self.main_window.show()

if __name__ == '__main__':
    EduMentor().run()