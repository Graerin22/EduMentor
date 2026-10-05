from datetime import datetime
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QTextBlockFormat
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from core.document_parser import DocumentParser
from core.ai_engine import AIWorker
from core.database import Database
from models.session import Session, ChatData

CURR_DIR = Path(__file__).resolve().parents[2]
UI_FILE_PATH = CURR_DIR / 'ui_designs' / 'chat_widget.ui'

class ChatWidget(QWidget):
    session_load_requested = pyqtSignal(object, int, int, bool)

    def __init__(self, db:Database, user_id):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.current_session = None
        self.chat_data = ChatData(chat_id=-1, session_id=-1,
                                  timestamp='', chat_name='', 
                                  filename='', document_text='')

        uic.loadUi(str(UI_FILE_PATH), self)
        
        self.upload_btn.clicked.connect(self.upload_file)
        self.newchat_btn.clicked.connect(self.create_new_chat)
        self.save_btn.clicked.connect(self.save_chat_session)
        self.send_btn.clicked.connect(self.send_message)

    def create_new_chat(self, is_deleted=False):
        if not is_deleted and (self.chat_data.chats and self.chat_data.document_text):
            reply = QMessageBox.question(self, 'Start New Chat', 
                                         'Start a new chat?\nYour current session will be saved first.',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            self.save_chat_session(silent=True)            

        self.current_session = None
        self.chat_data = ChatData(chat_id=-1, session_id=-1,
                                  timestamp='', chat_name='', 
                                  filename='', document_text='')
        self.session_load_requested.emit(None, 0, -1, False)

        self.upload_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.file_display.clear()
        self.ai_display.clear()
        self.input_text.clear()

    def save_chat_session(self, silent=False):
        if not self.chat_data.chats or not self.chat_data.document_text:
            if not silent:
                QMessageBox.warning(self, 'Save Failed',
                                    'Upload a document and send a message first.')
            return

        timestamp = datetime.now()
        if self.current_session:
            success, message = self.db.update_chat_session(timestamp, self.current_session, self.chat_data)
            if success:
                self.db.set_current_session(self.current_session)
                self.save_btn.setEnabled(False)

                if not silent:
                    QMessageBox.information(self, 'Success', 'Chat session is updated succesfully.')

                return
            else:
                QMessageBox.information(self, 'Save Failed', message + '\n\nPlease try again.')
                return
        else:
            self.current_session = self.db.save_chat_session(self.user_id, timestamp, self.chat_data)
            self.db.set_current_session(self.current_session)
            self.session_load_requested.emit(self.current_session, 0, -1, True)

            if not silent:
                QMessageBox.information(self, 'Saved', '💾 Quiz session saved!\n')

            self.save_btn.setEnabled(False)

    def load_session(self, session_obj: Session, flag):
        if flag:
            return

        self.current_session = session_obj
        if not self.current_session:
            return

        self.chat_data = session_obj.chat_data

        self.file_display.clear()
        self.file_display.append(f'📄 Loaded: {self.chat_data.filename}\n')

        cursor = self.file_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown('---')
        cursor.insertMarkdown(self.chat_data.document_text)
        self.file_display.setTextCursor(cursor)
        self.file_display.verticalScrollBar().setValue(0)
        
        self.send_btn.setEnabled(True)
        self.upload_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

        cursor = self.ai_display.textCursor()
        for msg in self.chat_data.chats:
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
        self.ai_display.setTextCursor(cursor)
        scroll_bar = self.ai_display.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def send_message(self):
        user_input = self.input_text.toPlainText().strip()
        if not user_input:
            return
        self.input_text.clear()
        if not self.chat_data.document_text:
            QMessageBox.warning(self, 'Send Failed',
                                'Upload a document first.')
            self.send_btn.setEnabled(True)
            return

        self.send_btn.setEnabled(False)
        self.newchat_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

        cursor = self.ai_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown("### 👤 You:&nbsp;\n")
        cursor.insertText(f'{user_input}\n')
        self.ai_display.setTextCursor(cursor)

        self.system_prompt = """Role: AI Tutor
Explain the concepts from the provided document using clear, universal language and practical analogies.
CRITICAL FORMATTING RULES:
1. Write all math formulas using clean plain text unicode operators and true subscripts/superscripts (e.g., aₙ = 6aₙ₋₁).
2. Do NOT use LaTeX, MathJax, or raw dollar sign notation ($ or $$).
3. Do NOT generate Markdown matrix tables using pipes (|)."""
        
        if not self.chat_data.chats:
            self.chat_data.chats.append({'role':'user', 'parts':f'Source Doc:\n{self.chat_data.document_text[:8000]}\n\nUser Question:\n{user_input}'})
        else:
            self.chat_data.chats.append({'role':'user', 'parts':user_input})

        self.ai_worker = AIWorker(self.chat_data.chats, self.system_prompt)
        self.ai_worker.finished.connect(self.on_ai_response)
        self.ai_worker.error.connect(self.on_ai_error)
        self.ai_worker.start()

    def on_ai_response(self, response):
        cursor = self.ai_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText('\n')
        cursor.insertMarkdown("### 🧠 AI Tutor:&nbsp;\n\n")

        cursor.insertMarkdown(response)
        cursor.insertBlock()
        cursor.setBlockFormat(QTextBlockFormat())
        cursor.setCharFormat(QTextCharFormat())
        cursor.insertText('\n')
        self.ai_display.setTextCursor(cursor)

        self.chat_data.chats.append({'role':'model', 'parts':response})
        self.send_btn.setEnabled(True)
        self.newchat_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def on_ai_error(self, error_msg):
        if '503 UNAVAILABLE' in error_msg:
            self.ai_display.append('⚠️ Google servers overloaded.')
            self.ai_display.append('You can try changing the AI model in the settings tab.\n\n')
        else:
            self.ai_display.append(f'❌ Error: {error_msg}\n\n')
        
        if self.chat_data.chats:
            self.chat_data.chats.pop()
        self.send_btn.setEnabled(True)
        self.newchat_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select File',
                        filter='Documents (*.pdf *.docx *.pptx *.csv)')

        if file_path:
            self.send_btn.setEnabled(False)
            self.parser = DocumentParser(file_path)
            self.parser.finished.connect(self.on_document_loaded)
            self.parser.error.connect(self.on_parser_error)
            self.parser.start()

    
    def on_document_loaded(self, text, filename):
        self.file_display.clear()
        self.chat_data.filename = filename
        self.chat_data.document_text = text
        self.file_display.append(f'📄 Loaded: {filename}\n')

        cursor = self.file_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown('---')
        cursor.insertMarkdown(text)
        self.file_display.setTextCursor(cursor)
        self.file_display.verticalScrollBar().setValue(0)
        
        self.send_btn.setEnabled(True)
        self.upload_btn.setEnabled(False)


    def on_parser_error(self, error_msg):
        self.file_display.append(f'❌ Error loading files: {error_msg}\n\n')
        self.send_btn.setEnabled(True)