import json
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QPushButton, QButtonGroup, QSlider
from core.quiz_generator import QuizWorker
from utils.sliding_stack import SlidingStackedWidget

CURRENT_DIR = Path(__file__).resolve().parent
UI_FILE_PATH = CURRENT_DIR / 'quiz_widget.ui'
TEMPLATE_PATH = CURRENT_DIR / 'question_widget.ui'

class QuizWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.messages = []
        self.main_window = main_window
        uic.loadUi(str(UI_FILE_PATH), self)

        try:
            self.document_text = self.main_window.document_text
            self.question_label.setText('✅ Generate Quiz')
            self.generate_btn.setEnabled(True)
        except Exception:
            self.question_label.setText('⚠️ Upload a document first at the Mentor Tab.')
            self.generate_btn.setEnabled(False)
            return

        self.inner_slide_stack = SlidingStackedWidget()
        self.inner_slide_stack.addWidget(self.question_widget)
        self.sliding_vlayout.addWidget(self.inner_slide_stack)

        self.next_btn.clicked.connect(self.go_next_question)
        self.prev_btn.clicked.connect(self.go_prev_question)
        self.generate_btn.clicked.connect(self.generate_quiz)
        self.bs_report_btn.clicked.connect(self.results)

    def generate_quiz(self):
        self.total_questions = self.num_quiz_slider.value()

        prompt = f"""Generate {self.total_questions} multiple-choice questions based on this document.
SOURCE DOC: {self.document_text[:8000]}
Return ONLY valid JSON in this exact format:
CRITICAL RULE: Prepend sequential numbers (1., 2.) to each question.
{{
    "questions": [
        {{
            "question": "Question text here?",
            "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            "correct": "A",
            "explanation": "Why this is correct"
        }}
    ]
}}"""

        self.messages.apppend({'role':'user', 'parts':prompt})
        self.quiz_worker = QuizWorker(self.messages)
        self.quiz_worker.finished.connect(self.generate_quiz_slides)
        self.quiz_worker.error.connect(self.on_ai_error)
        self.quiz_worker.start()

    def generate_quiz_slides(self, questions):
        self.answer_key = []
        for i in range(self.total_questions):
            slide_widget = QWidget()
            uic.load_ui(str(TEMPLATE_PATH), slide_widget)

            slide_widget.question_label.setText(questions[i]['question'])

            grouped_choices = slide_widget.choices_group.buttons()
            options_list = questions[i]['options']
            self.answer_key.append(questions[i]['correct'])

            for radio, option_text in zip(grouped_choices, options_list):
                radio.setText(option_text)

            self.inner_slide_stack.addWidget(slide_widget)
            slide_widget.send_btn.clicked.connect(self.confirm_answer)

        json_questions = json.dumps(questions, indent=4)
        model_content = self.quiz_worker({'role':'model', 'parts':json_questions})
        self.messages.append(model_content)

        self.go_next_question()
        self.inner_slide_stack.removeWidget(self.inner_slide_stack.widget(0))

    def confirm_answer(self):
        active_page = self.inner_slide_stack.currentWidget()
        curr_index = self.inner_slide_stack.currentIndex()

        active_page.send_btn.setEnabled(False)
        chosen_answer = active_page.choices_group.checkedButton().text()
        prompt = f"""Evaluate question {curr_index+1}:
User answer: {chosen_answer}
Confidence: {active_page.confidence_slider.value()}/5
Verify correctness. Provide the conceptual explanation. 
Adapt tone/feedback depth based on user confidence (e.g., address high confidence but wrong answer, or low confidence but right answer)."""
        self.messages.append({'role':'user', 'parts':prompt})

        self.correct_answers = []
        num_correct = 0
        if chosen_answer[0] == self.answer_key[curr_index]:
            self.correct_answers.append({f'No.{curr_index+1}':'Correct'})
            num_correct += 1
            self.score_label.setText(f'✅ Score : {num_correct}/{self.total_questions}')
        else:
            self.correct_answers.append({f'No.{curr_index+1}':'Wrong'})

        self.quiz_confirmer = QuizWorker(self.messages)
        self.quiz_confirmer.finished.connect(self.on_ai_response)
        self.quiz_confirmer.error.connect(self.on_ai_error)
        self.quiz_confirmer.start()

    def go_next_question(self):
        self.feedback_text.clear()
        curr = self.inner_slide_stack.currentIndex()
        self.inner_slide_stack.slide_to_index(curr+1)
        self.update_outer_dashboard()

        if curr < self.total_questions-1:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)
            self.bs_report_btn.setEnabled(True)

    def go_prev_question(self):
        curr = self.inner_slide_stack.currentIndex()
        self.inner_slide_stack.slide_to_index(curr-1)
        self.update_outer_dashboard()
        
        if curr > 0:
            self.prev_btn.setEnabled(True)
        else:
            self.prev_btn.setEnabled(False)

    def update_outer_dashboard(self):
        current_num = self.inner_slide_stack.currentIndex() + 1
        self.progress_label.setText(f'📊 Progress: {current_num}/{self.total_questions}')

    def results(self):
        curr = self.inner_slide_stack.currentIndex()
        self.inner_slide_stack.slide_to_index(curr+1)

        json_correct_answers = json.dumps(self.correct_answers, indent=4, sort_keys=True)
        prompt = f"""Analyze quiz results:
{json_correct_answers}
Generate:
1. Blind Spot Report: Identify weak content areas/gaps.
2. Action Plan: Concrete study steps to resolve gaps.
3. Resources: Specific topics, books, or web resources to review."""
        self.messages.append({'role':'user', 'content':prompt})

        self.result_worker = QuizWorker(self.messages)
        self.result_worker.finished.connect(self.on_ai_response)
        self.result_worker.error.connect(self.on_ai_error)
        self.result_worker.start()

        self.feedback_text.setMaximumHeight(16777215)
        self.inner_slide_stack.hide()

    def on_ai_response(self, response):
        self.feedback_text.append(response)

    def on_ai_error(self, error_msg):
        self.feedback_text.append(error_msg)