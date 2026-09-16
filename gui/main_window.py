from PyQt6.QtWidgets import QMainWindow, QTabWidget
from gui.chat_widget import ChatWidget
from gui.quiz_widget import QuizWidget
from gui.teach_widget import TeachWidget
#from gui.history_widget import HistoryWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduMentor - AI Teaching Assistant")
        self.setGeometry(300, 60, 1000, 700)

        tabs = QTabWidget()
        tabs.addTab(ChatWidget(self), '📖 Mentor')
        tabs.addTab(QuizWidget(self), '📝 Quiz')
        tabs.addTab(TeachWidget(self), '🗣️ Teach-back')
        #tabs.addTab(HistoryWidget(), '📚 History')
        self.setCentralWidget(tabs)