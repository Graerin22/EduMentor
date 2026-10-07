from pathlib import Path
from PyQt6 import uic
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QMessageBox
from core.ai_engine import AIWorker
from core.database import Database
from models.session import Session, TeachbackData

CURR_DIR = Path(__file__).resolve().parents[2]
UI_FILE_PATH = CURR_DIR / 'ui_designs' / 'teach_widget.ui'

class TeachWidget(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_session = None
        self.teachback_data = TeachbackData(teachback_id=-1, session_id=-1,
                                            timestamp='', teachback_name='',
                                            topic='', explanation='')

        uic.loadUi(str(UI_FILE_PATH), self)

        self.submit_btn.clicked.connect(self.submit_explanation)
        self.save_btn.clicked.connect(self.save_teachback_session)
        self.new_btn.clicked.connect(self.create_new_teachback)

    def create_new_teachback(self, is_deleted=False):
        if not is_deleted and self.teachback_data.teachback:
            reply = QMessageBox.question(self, 'New Teach-back',
                                         'Start a new teach-back?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.No:
                return
            else:
                save_reply = QMessageBox.question(self, 'Save Teach-back',
                                             'Do you want to save first?',
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                              QMessageBox.StandardButton.No)
                if save_reply == QMessageBox.StandardButton.Yes:
                    self.save_quiz_session(True)

        self._reset_attr()
        self.check_if_valid()

    def save_teachback_session(self, silent=False):
        if not self.teachback_data.teachback:
            return

        timestamp = datetime.now()
        if self.teachback_data.teachback_id != -1:
            success, message = self.db.update_teachback_session(timestamp.strftime('%B %d, %Y at %I:%M %p'), self.current_session, self.teachback_data)
            if success:
                self.save_btn.setEnabled(False)

                if not silent:
                    QMessageBox.information(self, 'Success', 'Teach-back session is updated succesfully.')

                return
            else:
                QMessageBox.information(self, 'Save Failed', message)
                return
        else:
            self.db.save_teachback_session(timestamp, self.current_session, self.teachback_data)

            if not silent:
                QMessageBox.information(self, 'Saved', '💾 Teach-back session saved!\n')
        
            self.save_btn.setEnabled(False)

    def load_session(self, session_obj: Session, item_idx):
        self.current_session = session_obj
        self._reset_attr()
        if not self.current_session or not session_obj.teachback_datas or item_idx < 0:
            return

        self.teachback_data = self.current_session.teachback_datas[item_idx]

        self.topic_input.setPlainText(self.teachback_data.topic)
        self.explanation_input.setPlainText(self.teachback_data.explanation)

        self.feedback_text.clear()
        cursor = self.feedback_text.textCursor()
        cursor.insertMarkdown(self.teachback_data.teachback[1]['parts'])
        self.feedback_text.setTextCursor(cursor)
        self.feedback_text.verticalScrollBar().setValue(0)

    def _reset_attr(self):
        self.teachback_data = TeachbackData(teachback_id=-1,
                                            session_id=self.current_session.session_id if self.current_session else -1,
                                            timestamp='', teachback_name='',
                                            topic='', explanation='')

        self.topic_input.clear()
        self.explanation_input.clear()
        self.feedback_text.clear()

    def check_if_valid(self):
        if self.feedback_text.toPlainText().strip():
            return
        if not self.current_session:
            self.feedback_text.setText('⚠️ Save a document and a message on the Mentor Tab first.')
            self.submit_btn.setEnabled(False)
            return
        
        self.feedback_text.setText('✅ You can now submit your topic explanation.')
        self.submit_btn.setEnabled(True)

    def submit_explanation(self):
        self.feedback_text.clear()
        self.teachback_data.topic = self.topic_input.toPlainText().strip()
        self.teachback_data.explanation = self.explanation_input.toPlainText().strip()

        if not self.teachback_data.topic or not self.teachback_data.explanation:
            self.feedback_text.setText('⚠️ Please enter both a topic and your explanation.')
            return

        self.submit_btn.setEnabled(False)
        self.new_btn.setEnabled(False)

        system_prompt = f"""Evaluate a student's explanation using the Feynman Technique criteria:
Provide feedback in this format:
1. Clarity (Score 1-10): How well did they explain it simply?
2. Accuracy (Score 1-10): Were the facts correct?
3. Analogies/Examples (Score 1-10): Did they use good examples?
4. What they got right: List 2-3 strengths
5. What they missed: List 2-3 concepts they should add
6. Overall Score: X/10
NOTICE: DO NOT EVALUATE THE SOURCE(USE IT AS A GUIDE), JUST THE EXPLANATION.
CRITICAL FORMATTING RULES:
1. Write all math formulas using clean plain text unicode operators and true subscripts/superscripts (e.g., aₙ = 6aₙ₋₁).
2. Do NOT use LaTeX, MathJax, or raw dollar sign notation ($ or $$).
"""
        
        if not self.teachback_data.teachback:
            self.teachback_data.teachback.append({'role':'user', 'parts':f'Source: {self.current_session.chat_data.document_text}\nTopic: {self.teachback_data.topic}\nStudent\'s Explanation: {self.teachback_data.explanation}'})
        else:
            self.teachback_data.teachback.append({'role':'user','parts':f'Topic: {self.teachback_data.topic}\nStudent\'s Explanation: {self.teachback_data.explanation}'})

        self.ai_worker = AIWorker(self.teachback_data.teachback, system_prompt)
        self.ai_worker.finished.connect(self.on_ai_response)
        self.ai_worker.error.connect(self.on_ai_error)
        self.ai_worker.start()

    def on_ai_response(self, response):
        cursor = self.feedback_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertMarkdown(response)
        self.feedback_text.setTextCursor(cursor)

        self.teachback_data.teachback.append({'role':'model', 'parts':response})
        self.save_btn.setEnabled(True)
        self.new_btn.setEnabled(True)

    def on_ai_error(self, error_msg):
        if '503 UNAVAILABLE' in error_msg:
            self.feedback_text.append('⚠️ Google servers overloaded.')
            self.feedback_text.append(' You can try changing the AI model in the settings tab.\n')
        else:
            self.feedback_text.append(f'❌ Error: {error_msg}\n\nPlease try again.')
        
        if self.teachback_data.teachback:
            self.teachback_data.teachback.pop()
        self.submit_btn.setEnabled(True)
        self.new_btn.setEnabled(True)