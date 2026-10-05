import json
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem, QInputDialog, QMessageBox
from PyQt6.QtGui import QTextCharFormat, QTextBlockFormat
from PyQt6.QtCore import Qt, pyqtSignal
from core.database import Database
from models.session import Session, QuizData, TeachbackData, ChatData

CURR_DIR = Path(__file__).resolve().parents[2]
UI_FILE_PATH = CURR_DIR / 'ui_designs' / 'history_widget.ui'

class HistoryWidget(QWidget):
    session_delete_requested = pyqtSignal()
    session_load_requested = pyqtSignal(object, int, int, bool)

    def __init__(self, db: Database, user_id):
        super().__init__()
        self.db = db
        self.user_id = user_id

        uic.loadUi(str(UI_FILE_PATH), self)

        self.selected_parent_item: Session = None
        self.selected_item = None

        self.sessions_list.itemClicked.connect(self.on_item_clicked)
        self.sessions_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.load_btn.clicked.connect(self.request_load_selected)
        self.refresh_btn.clicked.connect(self.refresh_history)
        self.rename_btn.clicked.connect(self.rename_selected)
        self.delete_btn.clicked.connect(self.delete_selected)

    def refresh_history(self):
        self.sessions_list.clear()
        self.selected_parent_item = None
        self.selected_item = None

        sessions = self.db.get_all_sessions(self.user_id)

        if not sessions:
            item = QTreeWidgetItem(['(no sessions yet)'])
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.sessions_list.addTopLevelItem(item)
            self.update_btn_state()
            return

        for session in sessions:
            marker = '⭐ ' if session.is_current else ''
            session_name = f'{marker}{session.session_name}'

            session_parent = QTreeWidgetItem([session_name])
            session_parent.setData(0, Qt.ItemDataRole.UserRole, session)

            chat_child_name = session.chat_data.chat_name
            QTreeWidgetItem(session_parent, [chat_child_name]).setData(0, Qt.ItemDataRole.UserRole, session.chat_data)

            quiz_child = QTreeWidgetItem(session_parent, ['Quizzes'])
            for quiz in session.quiz_datas:
                name = quiz.quiz_name
                QTreeWidgetItem(quiz_child, [name]).setData(0, Qt.ItemDataRole.UserRole, quiz)

            teachback_child = QTreeWidgetItem(session_parent, ['Teachbacks'])
            for teachback in session.teachback_datas:
                name = teachback.teachback_name
                QTreeWidgetItem(teachback_child, [name]).setData(0, Qt.ItemDataRole.UserRole, teachback)

            self.sessions_list.addTopLevelItem(session_parent)

        self.update_btn_state()

    def update_btn_state(self):
        has_selection = self.selected_item is not None
        self.load_btn.setEnabled(has_selection)
        self.rename_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def on_item_clicked(self, item, column):
        self.preview_display.clear()
        if item.text(column) in ['Quizzes', 'Teachbacks']:
            self.selected_parent_item = None
            self.selected_item = None
            self.update_btn_state()
            return
        if item.parent() is None:
            self.selected_parent_item = item.data(column, Qt.ItemDataRole.UserRole)
            self.selected_item = self.selected_parent_item
            self.update_btn_state()
            return
        
        self.selected_item = item.data(column, Qt.ItemDataRole.UserRole)
        branch = item.parent().text(column)
        if branch == 'Quizzes':
            self.selected_parent_item = item.parent().parent().data(column, Qt.ItemDataRole.UserRole)
            self.display_quiz_details(self.selected_item)
        elif branch == 'Teachbacks':
            self.selected_parent_item = item.parent().parent().data(column, Qt.ItemDataRole.UserRole)
            self.display_teachback_details(self.selected_item)
        else:
            self.selected_parent_item = item.parent().data(column, Qt.ItemDataRole.UserRole)
            self.display_chat_details(self.selected_item)

        self.update_btn_state()

    def on_item_double_clicked(self, item, column):
        if item.text(column) in ['Quizzes', 'Teachbacks']:
            self.selected_parent_item = None
            self.selected_item = None
            self.update_btn_state()
            return
        if item.parent() is None:
            self.selected_parent_item = item.data(column, Qt.ItemDataRole.UserRole)
            self.selected_item = self.selected_parent_item
            self.request_load_selected()
            return

        branch = item.parent().text(column)
        self.selected_item = item.data(column, Qt.ItemDataRole.UserRole)
        if branch in ['Quizzes', 'Teachbacks']:
            self.selected_parent_item = item.parent().parent().data(column, Qt.ItemDataRole.UserRole)
        else:
            self.selected_parent_item = item.parent().data(column, Qt.ItemDataRole.UserRole)
        
        self.request_load_selected()

    def display_chat_details(self, chat_data: ChatData):
        self.preview_display.append(f"📝 Chat: {chat_data.chat_name}")
        self.preview_display.append(f'📂 Uploaded file name: {chat_data.filename}')
        self.preview_display.append(f'📃 No# of messages: {chat_data.chat_length()}')
        self.preview_display.append(f'🕒 Last open: {chat_data.timestamp}\n\n')

        cursor = self.preview_display.textCursor()
        for msg in chat_data.chats:
            if msg['role'] == 'user':
                parts = msg['parts']
                if 'User Question:' in parts:
                    parts = parts.split('User Question:', 1)[1].strip()
            
                cursor.insertMarkdown("### 👤 You:&nbsp;\n")
                cursor.insertText(f'{parts}\n\n')
            else:
                cursor.insertMarkdown("### 🧠 AI Tutor:&nbsp;\n\n")
                cursor.insertMarkdown(msg['parts'])
                cursor.insertBlock()
                cursor.setBlockFormat(QTextBlockFormat())
                cursor.setCharFormat(QTextCharFormat())
                cursor.insertText('\n')
        self.preview_display.setTextCursor(cursor)
        self.preview_display.verticalScrollBar().setValue(0)

    def display_quiz_details(self, quiz_data: QuizData):
        self.preview_display.append(f"📝 Quiz: {quiz_data.quiz_name}")
        self.preview_display.append(f"🕒 Last open: {quiz_data.timestamp}\n")

        items = json.loads(quiz_data.quiz[1]['parts'])
        total = len(items)

        cursor = self.preview_display.textCursor()
        for i in range(total):
            cursor.insertMarkdown(f'{items[i]['question']}\n\n')
            cursor.insertBlock()
            cursor.setBlockFormat(QTextBlockFormat())
            cursor.setCharFormat(QTextCharFormat())
            cursor.insertText('\n')

            for option in items[i]['options']:
                cursor.insertText(f"{option}\n")
                

            total_results = len(quiz_data.quiz_result)
            if i < total_results:
                result_item = quiz_data.quiz_result[i]
                key = f'No.{i+1}'

                user_choice = result_item[key][0]
                cursor.insertText(f'\n❓ Your answer: {user_choice}\n')
            else:
                cursor.insertText(f"\n❓ Your answer: 'Unanswered'\n")

            cursor.insertText(f"✅ Correct: {items[i]['correct']}\n")

            if i < total_results:
                cursor.insertMarkdown("### 🗪 Feedback:\n\n")
                cursor.insertMarkdown(f"\n{quiz_data.feedbacks[i]}")
                cursor.insertBlock()
                cursor.setBlockFormat(QTextBlockFormat())
                cursor.setCharFormat(QTextCharFormat())

                if i+1 == total:
                    cursor.inserText('\n')
                    cursor.insertMarkdown('### 📊 Blind spot result:\n\n')
                    cursor.insertMarkdown('\n{quiz_data.feedbacks[i]}')
                    cursor.insertBlock()
                    cursor.setBlockFormat(QTextBlockFormat())
                    cursor.setCharFormat(QTextCharFormat())
            else:
                cursor.insertMarkdown('### 🗪 Feedback:&nbsp;\n')
                cursor.insertText("'No Feedback'\n")
                cursor.insertMarkdown(f"### 💡 Question explanation:\n\n")
                cursor.insertMarkdown(f"\n{items[i]['explanation']}")
                cursor.insertBlock()
                cursor.setBlockFormat(QTextBlockFormat())
                cursor.setCharFormat(QTextCharFormat())

        self.preview_display.setTextCursor(cursor)
        self.preview_display.verticalScrollBar().setValue(0)
        

    def display_teachback_details(self, teachback_data: TeachbackData):
        self.preview_display.append(f"🗣️ Teach-back: {teachback_data.teachback_name}")
        self.preview_display.append(f'🕒 Last update: {teachback_data.timestamp}\n')

        text: str = teachback_data.teachback[0]['parts']
        marker_topic = 'Topic: '
        marker_expl = "Student's Explanation: "
        
        i_topic = text.find(marker_topic)
        i_expl = text.find(marker_expl)
        
        topic = text[i_topic+len(marker_topic):i_expl].strip()
        explanation = text[i_expl + len(marker_expl):].strip()
        
        self.preview_display.append(f'💬 Topic: {topic}')
        self.preview_display.append(f'💡 Your Explanation:\n{explanation}\n\n')
        
        cursor = self.preview_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown("### 📝 Feedback:&nbsp;\n")
        cursor.insertBlock()
        cursor.setBlockFormat(QTextBlockFormat())
        cursor.setCharFormat(QTextCharFormat())
        cursor.insertMarkdown(teachback_data.teachback[1]['parts'])
        self.preview_display.setTextCursor(cursor)
        self.preview_display.verticalScrollBar().setValue(0)

    def request_load_selected(self):
        if not self.selected_item:
            QMessageBox.warning(self, 'Load Failed', 'Select a data first.')
            return

        if isinstance(self.selected_item, QuizData):
            tab_idx = 1
            quiz_idx = self.selected_parent_item.quiz_datas.index(self.selected_item)
            self.session_load_requested.emit(self.selected_parent_item, tab_idx, quiz_idx, False)
        elif isinstance(self.selected_item, TeachbackData):
            tab_idx = 2
            teachback_idx = self.selected_parent_item.teachback_datas.index(self.selected_item)
            self.session_load_requested.emit(self.selected_parent_item, tab_idx, teachback_idx, False)
        else:
            tab_idx = 0
            self.session_load_requested.emit(self.selected_parent_item, tab_idx, -1, False)
        
        self.db.set_current_session(self.selected_parent_item)

        self.selected_parent_item = None
        self.selected_item = None
        self.refresh_history()

    def rename_selected(self):
        if not self.selected_item:
            QMessageBox.warning(self, 'Rename Failed', 'Select a data first.')
            return

        if isinstance(self.selected_item, Session):
            curr_name = self.selected_item.session_name
            new_name, ok = QInputDialog.getText(self, 'Rename Session',
                                                        'Enter a new name: ', text=curr_name)
            if not ok or not new_name.strip():
                return

            success, message = self.db.rename_session(new_name, self.selected_item)
            if success:
                QMessageBox.information(self, 'Renamed', f'Session renamed to:\n{new_name}')
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Rename Failed', message)

        elif isinstance(self.selected_item, ChatData):
            curr_name = self.selected_item.chat_name
            new_name, ok = QInputDialog.getText(self, 'Rename Chat Session',
                                                        'Enter a new name: ', text=curr_name)
            if not ok or not new_name.strip():
                return

            success, message = self.db.rename_chat_data(new_name, self.selected_item)
            if success:
                QMessageBox.information(self, 'Renamed', f'Chat Session renamed to:\n{new_name}')
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Rename Failed', message)

        elif isinstance(self.selected_item, QuizData):
            curr_name = self.selected_item.quiz_name
            new_name, ok = QInputDialog.getText(self, 'Rename Quiz Session',
                                                        'Enter a new name: ', text=curr_name)
            if not ok or not new_name.strip():
                return

            success, message = self.db.rename_quiz_data(new_name, self.selected_item)
            if success:
                QMessageBox.information(self, 'Renamed', f'Quiz Session renamed to:\n{new_name}')
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Rename Failed', message)

        elif isinstance(self.selected_item, TeachbackData):
            curr_name = self.selected_item.teachback_name
            new_name, ok = QInputDialog.getText(self, 'Rename Teachback Session',
                                                        'Enter a new name: ', text=curr_name)
            if not ok or not new_name.strip():
                return

            success, message = self.db.rename_teachback_data(new_name, self.selected_item)
            if success:
                QMessageBox.information(self, 'Renamed', f'Teachback Session renamed to:\n{new_name}')
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Rename Failed', message)

    def delete_selected(self):
        if not self.selected_item:
            QMessageBox.warning(self, 'Delete Failed', 'Select a data first.')
            return

        if isinstance(self.selected_item, Session):
            session_name = self.selected_item.session_name
            reply = QMessageBox.question(self, 'Delete Session',
                                         f'Are you sure you want to delete:\n\n{session_name}\n\n',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply != QMessageBox.StandardButton.Yes:
                return

            success, message = self.db.delete_session(self.selected_item)
            if success:
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Delete Failed', message)

        elif isinstance(self.selected_item, ChatData):
            chat_name = self.selected_item.chat_name
            reply = QMessageBox.question(self, 'Delete Chat Session',
                                         f'Are you sure you want to delete:\n\n{chat_name}\n\nCurrent Session will be deleted too.',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply != QMessageBox.StandardButton.Yes:
                return

            success, message = self.db.delete_chat_data(self.selected_item)
            if success:
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Delete Failed', message)

        elif isinstance(self.selected_item, QuizData):
            quiz_name = self.selected_item.quiz_name
            reply = QMessageBox.question(self, 'Delete Chat Session',
                                         f'Are you sure you want to delete:\n\n{quiz_name}\n\n',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply != QMessageBox.StandardButton.Yes:
                return

            success, message = self.db.delete_quiz_data(self.selected_item)
            if success:
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Delete Failed', message)

        elif isinstance(self.selected_item, TeachbackData):
            teachback_name = self.selected_item.teachback_name
            reply = QMessageBox.question(self, 'Delete Teachback Session',
                                         f'Are you sure you want to delete:\n\n{teachback_name}\n\n',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply != QMessageBox.StandardButton.Yes:
                return

            success, message = self.db.delete_teachback_data(self.selected_item)
            if success:
                self.refresh_history()
            else:
                QMessageBox.warning(self, 'Delete Failed', message)

        self.session_delete_requested.emit()