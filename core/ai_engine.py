from google import genai
from google.genai import types
from PyQt6.QtCore import QThread, pyqtSignal
from utils.config import get_model

class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, messages, system_prompt):
        super().__init__()
        self.messages = messages
        self.system_prompt = system_prompt

    def run(self):
        try:
            client = genai.Client()

            content = self.to_content(self.messages[-1])
            response = client.models.generate_content(
                model=get_model(),
                contents=content,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.4
                )
            )

            self.finished.emit(response.text)
            
        except Exception as e:
            self.error.emit(str(e))

    def to_content(self, content):
        google_parts = [types.Part.from_text(text=content['parts'])]
        google_content = types.Content(role=content['role'], parts=google_parts)
        return google_content