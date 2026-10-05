import json
from pathlib import Path
from PyQt6 import uic
from datetime import datetime
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QMessageBox
from core.quiz_generator import QuizWorker
from core.ai_engine import AIWorker
from core.database import Database
from utils.sliding_stack import SlidingStackedWidget
from models.session import Session, QuizData

CURR_DIR = Path(__file__).resolve().parents[2]
UI_FILE_PATH = CURR_DIR / 'ui_designs' / 'quiz_widget.ui'
TEMPLATE_PATH = CURR_DIR / 'ui_designs' / 'question_widget.ui'

class QuizWidget(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.current_session = None
        self.quiz_data = QuizData(quiz_id=-1, session_id=-1,
                                  timestamp='', quiz_name='',
                                  quiz_score=0)

        uic.loadUi(str(UI_FILE_PATH), self)

        self.next_btn.clicked.connect(self.go_next_question)
        self.prev_btn.clicked.connect(self.go_prev_question)
        self.generate_btn.clicked.connect(self.generate_quiz)
        self.bs_report_btn.clicked.connect(self.final_result)
        self.save_btn.clicked.connect(self.save_quiz_session)
        self.new_quiz_btn.clicked.connect(self.create_new_quiz)

        self.inner_slide_stack = SlidingStackedWidget()
        self.inner_slide_stack.addWidget(self.generate_widget)
        self.sliding_vlayout.addWidget(self.inner_slide_stack)

    def create_new_quiz(self, is_deleted=False):
        if not is_deleted and self.quiz_data.quiz:
            reply = QMessageBox.question(self, 'New Quiz',
                                         'Start a new quiz?\nYour current quiz will be saved first.',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
            
            self.save_quiz_session(True)
        
        self._reset_attr()
        self.check_if_valid()

    def save_quiz_session(self, silent=False):
        if not self.quiz_data.quiz:
            return

        timestamp = datetime.now()
        if self.quiz_data.quiz_id != -1:
            success, message = self.db.update_quiz_session(timestamp, self.current_session, self.quiz_data)
            if success:
                self.save_btn.setEnabled(False)

                if not silent:
                    QMessageBox.information(self, 'Success', 'Chat session is updated succesfully.')

                return
            else:
                QMessageBox.information(self, 'Save Failed', message)
                return
        else:
            self.db.save_quiz_session(timestamp, self.current_session, self.quiz_data)

            if not silent:
                QMessageBox.information(self, 'Saved', '💾 Quiz session saved!\n')
            
            self.save_btn.setEnabled(False)
        

    def load_session(self, session_obj: Session, item_idx: int):
        self.current_session = session_obj
        self._reset_attr()
        if not self.current_session or not session_obj.quiz_datas:
            return

        self.quiz_data = session_obj.quiz_datas[item_idx]

        self.total_questions = self.quiz_data.quiz_length()
        self.last_answered_index = -1
        self.generate_quiz_slides(json.loads(self.quiz_data.quiz[1]['parts']))

    def _reset_attr(self):
        if self.inner_slide_stack.count() > 1:
            while self.inner_slide_stack.count() > 0:
                widget = self.inner_slide_stack.widget(0)
                self.inner_slide_stack.removeWidget(widget)
                widget.deleteLater()

            self.inner_slide_stack.addWidget(self.generate_widget)

        self.quiz_data = QuizData(quiz_id=-1,
                                  session_id=self.current_session.session_id if self.current_session else -1,
                                  timestamp='', quiz_name='', quiz_score=0)

        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.bs_report_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.inner_slide_stack.show()
        self.num_items_input.setReadOnly(False)
        self.feedback_text.clear()
        self.feedback_text.setMaximumHeight(200)
        self.progress_label.setText('📊 Progress: 0/0')
        self.score_label.setText('✅ Score: 0/0')

    def check_if_valid(self):
        if self.quiz_data.quiz:
            return
        if not self.current_session:
            self.feedback_text.setText('⚠️ Save a document and a message on the Mentor Tab first.')
            self.generate_btn.setEnabled(False)
            return
        
        self.feedback_text.setText('✅ You can generate quiz.')
        self.generate_btn.setEnabled(True)

    def generate_quiz(self):
        try:
            total_questions = int(self.num_items_input.text())
        except ValueError:
            QMessageBox.warning(self, 'Invalid Input', 'Please enter a number.')
            self.num_items_input.clear()
            return
        if total_questions <= 0 or total_questions > 20:
            QMessageBox.warning(self, 'Invalid number', 'Please enter a number between 1 and 20.')
            self.num_items_input.clear()
            return

        self.num_items_input.setReadOnly(True)
        self.generate_btn.setEnabled(False)
        self.new_quiz_btn.setEnabled(False)
        self.feedback_text.clear()
        self.total_questions = total_questions
        self.last_answered_index = -1

        content = f"""Generate {self.total_questions} multiple-choice questions based on this document.
SOURCE DOC: {self.current_session.chat_data.document_text[:8000]}
Return ONLY valid JSON in this exact format:
{{
    "questions": [
        {{
            "question": "Question text here?",
            "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            "correct": "A",
            "explanation": "Why this is correct"
        }}
    ]
}}
CRITICAL RULES:
1. Prepend sequential numbers (1., 2.) to each question.
2. Write all math formulas using clean plain text unicode operators and true subscripts/superscripts (e.g., aₙ = 6aₙ₋₁).
3. Do NOT use LaTeX, MathJax, or raw dollar sign notation ($ or $$).
4. Do NOT generate Markdown matrix tables using pipes (|).
"""
        self.quiz_data.quiz.append({'role':'user', 'parts':content})
        self.quiz_worker = QuizWorker(self.quiz_data.quiz)
        self.quiz_worker.finished.connect(self.generate_quiz_slides)
        self.quiz_worker.error.connect(self.on_ai_error)
        self.quiz_worker.start()

    def generate_quiz_slides(self, questions):
        print(questions)
        self.answer_key = []
        for i in range(self.total_questions):
            slide_widget = QWidget()
            uic.loadUi(str(TEMPLATE_PATH), slide_widget)

            slide_widget.question_label.setText(questions[i]['question'])

            grouped_choices = slide_widget.choices_group.buttons()
            options_list = questions[i]['options']
            for radio_btn, option_text in zip(grouped_choices, options_list):
                radio_btn.setText(option_text)

            self.answer_key.append(questions[i]['correct'])
            self.inner_slide_stack.addWidget(slide_widget)
            slide_widget.submit_answer_btn.clicked.connect(self.confirm_answer)

        self.quiz_data.quiz.append({'role':'model', 'parts':json.dumps(questions)})

        self.inner_slide_stack.slide_to_index(1)
        QTimer.singleShot(600, lambda: self.inner_slide_stack.removeWidget(self.inner_slide_stack.widget(0)))

    def confirm_answer(self):
        active_page = self.inner_slide_stack.currentWidget()
        selected_btn = active_page.choices_group.checkedButton()
        if selected_btn is None:
            QMessageBox.warning(self, 'Selection Required', 'Please select an option before submitting.')
            return

        chosen_answer = selected_btn.text()[0]

        curr = self.inner_slide_stack.currentIndex()
        active_page.submit_answer_btn.setEnabled(False)
        active_page.confidence_slider.setEnabled(False)
        self.new_quiz_btn.setEnabled(False)
        for btn in active_page.choices_group.buttons():
            btn.setEnabled(False)

        prompt = f"""Evaluate question {curr+1}:
User answer: {chosen_answer}
Confidence: {active_page.confidence_slider.value()}/5
Verify correctness. Provide the conceptual explanation. 
Adapt tone/feedback depth based on user confidence (e.g., address high confidence but wrong answer, or low confidence but right answer).
CRITICAL FORMATTING RULES:
1. Write all math formulas using clean plain text unicode operators and true subscripts/superscripts (e.g., aₙ = 6aₙ₋₁).
2. Do NOT use LaTeX, MathJax, or raw dollar sign notation ($ or $$).
3. Do NOT generate Markdown matrix tables using pipes (|)."""
        self.quiz_data.quiz.append({'role':'user', 'parts':prompt})

        self.answer_confirmer = AIWorker(self.quiz_data.quiz)
        self.answer_confirmer.req_data = {'req_type':'confirm', 'attr':[curr, chosen_answer, active_page]}
        self.answer_confirmer.finished.connect(self.on_ai_response)
        self.answer_confirmer.error.connect(self.on_ai_error)
        self.answer_confirmer.start()

    def update_outer_dashboard(self):
        self.progress_label.setText(f'📊 Progress: {self.last_answered_index+1}/{self.total_questions}')
        self.score_label.setText(f'✅ Score: {self.quiz_data.quiz_score}/{self.total_questions}')

    def go_next_question(self):
        next_idx = self.inner_slide_stack.currentIndex() + 1

        if next_idx <= self.last_answered_index:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)

        if next_idx < len(self.quiz_data.feedbacks):
            self.set_feedback(self.quiz_data.feedbacks[next_idx])

        self.inner_slide_stack.slide_to_index(next_idx)

        def _update():
            self.prev_btn.setEnabled(True)

        QTimer.singleShot(600, lambda: _update())

    def go_prev_question(self):
        prev_idx = self.inner_slide_stack.currentIndex() - 1
        
        if prev_idx > 0:
            self.prev_btn.setEnabled(True)
        else:
            self.prev_btn.setEnabled(False)

        if prev_idx >= 0 and prev_idx < len(self.quiz_data.feedbacks):
            self.set_feedback(self.quiz_data.feedbacks[prev_idx])

        self.inner_slide_stack.slide_to_index(prev_idx)

        def _update():
            self.next_btn.setEnabled(True)

        QTimer.singleShot(600, lambda: _update())

    def final_result(self):
        self.bs_report_btn.setEnabled(False)
        self.new_quiz_btn.setEnabled(False)
        json_quiz_result = json.dumps(self.quiz_data.quiz_result, indent=4, sort_keys=True)
        prompt = f"""Analyze quiz results:
{json_quiz_result}
Generate:
1. Blind Spot Report: Identify weak content areas/gaps.
2. Action Plan: Concrete study steps to resolve gaps.
3. Resources: Specific topics, books, or web resources to review.
CRITICAL FORMATTING RULES:
1. Write all math formulas using clean plain text unicode operators and true subscripts/superscripts (e.g., aₙ = 6aₙ₋₁).
2. Do NOT use LaTeX, MathJax, or raw dollar sign notation ($ or $$).
3. Do NOT generate Markdown matrix tables using pipes (|)."""
        self.quiz_data.quiz.append({'role':'user', 'parts':prompt})

        self.result_worker = AIWorker(self.quiz_data.quiz)
        self.result_worker.req_data = {'req_type':'result'}
        self.result_worker.finished.connect(self.on_ai_response)
        self.result_worker.error.connect(self.on_ai_error)
        self.result_worker.start()

    def set_feedback(self, response):
        self.feedback_text.clear()
        cursor = self.feedback_text.textCursor()
        cursor.insertMarkdown(response)
        self.feedback_text.setTextCursor(cursor)
        self.feedback_text.verticalScrollBar().setValue(0)
        self.quiz_data.feedbacks.append(response)

    def on_ai_response(self, response):
        worker = self.sender()
        req_data = getattr(worker, 'req_data')

        self.set_feedback(response)
        if req_data['req_type'] == 'confirm':
            self.last_answered_index = req_data['attr'][0]
            chosen_answer = req_data['attr'][1]
            if chosen_answer.startswith(self.answer_key[self.last_answered_index]):
                self.quiz_data.quiz_result.append({f'No.{self.last_answered_index+1}':[chosen_answer, 'Correct']})
                self.quiz_data.quiz_score += 1
            else:
                self.quiz_data.quiz_result.append({f'No.{self.last_answered_index+1}':[chosen_answer, 'Wrong']})

            self.update_outer_dashboard()

            if self.last_answered_index == self.total_questions-1:
                self.bs_report_btn.setEnabled(True)
                return
            
            self.next_btn.setEnabled(True)

        elif req_data['req_type'] == 'result':
            self.feedback_text.setMaximumHeight(16777215)
            self.inner_slide_stack.hide()

            self.save_btn.setEnabled(True)
            self.prev_btn.setEnabled(False)

        self.quiz_data.quiz.append({'role':'model', 'parts':response})
        self.new_quiz_btn.setEnabled(True)

    def on_ai_error(self, error_msg):
        worker = self.sender()
        req_data = getattr(worker, 'req_data', None)

        if not req_data:
            self.num_items_input.setReadOnly(False)
            self.num_items_input.clear()
            self.generate_btn.setEnabled(True)
        elif req_data['req_type'] == 'confirm':
            curr_widget = req_data['attr'][2]
            curr_widget.submit_answer_btn.setEnabled(True)

        elif req_data['req_type'] == 'result':
            self.bs_report_btn.setEnabled(True)

        print(error_msg)
        self.feedback_text.clear()
        if '503 UNAVAILABLE' in error_msg:
            self.feedback_text.append('⚠️ Google servers overloaded.')
            self.feedback_text.append(' You can try changing the AI model in the settings tab.\n')
        else:
            self.feedback_text.append(f'❌ Error: {error_msg}\n\nPlease try again.')

        if self.quiz_data.quiz:
            self.quiz_data.quiz.pop()
        self.new_quiz_btn.setEnabled(True)
