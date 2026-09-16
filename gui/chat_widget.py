from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog
from core.document_parser import DocumentParser
from core.ai_engine import AIWorker

CURRENT_DIR = Path(__file__).resolve().parent
UI_FILE_PATH = CURRENT_DIR / 'chat_widget.ui'

class ChatWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        uic.loadUi(str(UI_FILE_PATH), self)

        self.messages = []
        self.document_text = ''
        
        self.upload_btn.clicked.connect(self.upload_file)
        self.send_btn.clicked.connect(self.send_message)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select File',
                        filter='Documents (*.pdf *.docx *.pptx *.csv)')

        if file_path:
            self.parser = DocumentParser(file_path)
            self.parser.finished.connect(self.on_document_loaded)
            self.parser.error.connect(self.on_parser_error)
            self.parser.start()

    def send_message(self):
        user_input = self.input_text.toPlainText().strip()
        if not user_input:
            return

        cursor = self.ai_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown("### 👤 You:&nbsp;\n")
        cursor.insertMarkdown(f"{user_input}")
        cursor.insertText('\n\n')
        self.ai_display.setTextCursor(cursor)
        
        self.input_text.clear()
        self.send_btn.setEnabled(False)

        if not self.document_text:
            self.ai_display.append(f'⚠️ Please upload a document first.\n')
            self.send_btn.setEnabled(True)
            return

        if not self.messages:
            system_prompt = """Role: AI Tutor
Explain the concepts from the provided document using clear, universal language and practical analogies.
CRITICAL FORMATTING RULES:
1. Write all math formulas using clean plain text unicode operators and true subscripts/superscripts (e.g., aₙ = 6aₙ₋₁).
2. Do NOT use LaTeX, MathJax, or raw dollar sign notation ($ or $$).
3. Do NOT generate Markdown matrix tables using pipes (|)."""
            self.messages.append({'role':'user', 'parts':f'Source Doc:\n{self.document_text[:8000]}\n\nUser Question:\n{user_input}'})
        else:
            self.messages.append({'role':'user', 'parts':user_input})

        self.ai_worker = AIWorker(self.messages, system_prompt)
        self.ai_worker.finished.connect(self.on_ai_response)
        self.ai_worker.error.connect(self.on_ai_error)
        self.ai_worker.start()

    def on_document_loaded(self, text, filename):
        self.file_display.clear()
        self.document_text = text
        self.main_window.document_text = text
        self.document_metadata = filename
        self.file_display.appendPlainText(f'📄 Loaded: {filename}')

    def on_ai_response(self, response):
        cursor = self.ai_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown("### 🧠 AI Tutor:&nbsp;\n")
        cursor.insertMarkdown(response)
        cursor.insertText('\n\n')
        self.ai_display.setTextCursor(cursor)

        model_content = self.ai_worker.to_content({'role':'model', 'parts':response})
        self.messages.append(model_content)
        
        self.send_btn.setEnabled(True)

    def on_parser_error(self, error_msg):
        self.file_display.appendPlainText(f'❌ Error loading files: {error_msg}\n')

    def on_ai_error(self, error_msg):
        self.ai_display.append(f'❌ Error: {error_msg}\n')
        self.send_btn.setEnabled(True)