from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from core.ai_engine import AIWorker

CURRENT_DIR = Path(__file__).resolve().parent
UI_FILE_PATH = CURRENT_DIR / 'teach_widget.ui'

class TeachWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()

        uic.loadUi(str(UI_FILE_PATH), self)
        self.main_window = main_window

        self.messages = []

        try:
            self.document_text = self.main_window.document_text
            self.submit_btn.setEnabled(False)
        except Exception:
            self.feedback_text.setText('⚠️ Add document in the Mentor tab first for better accuracy.')
            return

        self.submit_btn.clicked.connect(self.submit_explanation)

    def submit_explanation(self):
        topic = self.topic_input.toPlainText().strip()
        explanation = self.explanation_input.toPlaintext().strip()

        self.feedback_text.clear()
        if not topic or not explanation:
            self.feedback_text.setText('⚠️ Please enter both a topic and your explanation.')
            return

        if not self.messages:
            system_prompt = f"""Evaluate a student's explanation using the Feynman Technique criteria:
Provide feedback in this format:
1. Clarity (Score 1-10): How well did they explain it simply?
2. Accuracy (Score 1-10): Were the facts correct?
3. Analogies/Examples (Score 1-10): Did they use good examples?
4. What they got right: List 2-3 strengths
5. What they missed: List 2-3 concepts they should add
6. Overall Score: X/10"""
            self.messages.append({'role':'user', 'parts':f'Source: {self.document_text}\nTopic: {topic}\nStudent\'s Explanation: {explanation}'})
        else:
            self.messages.append({'role':'user','parts':f'Topic: {topic}\nStudent\'s Explanation: {explanation}'})

        self.ai_worker = AIWorker(self.messages, system_prompt)
        self.ai_worker.finished.connect(self.on_ai_response)
        self.ai_worker.error.connect(self.on_ai_error)
        self.ai_worker.start()

    def on_ai_response(self, response):
        self.feedback_text.clear()
        cursor = self.feedback_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown(response)
        self.feedback_text.setTextCursor(cursor)

        model_content = self.ai_worker.to_content({'role':'model', 'parts':response})
        self.messages.append(model_content)
        
        self.send_btn.setEnabled(True)

    def on_ai_error(self, error_msg):
        self.ai_display.append(f'❌ Error: {error_msg}\n')
        self.send_btn.setEnabled(True)