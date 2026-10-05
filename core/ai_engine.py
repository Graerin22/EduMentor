from google import genai
from google.genai import types
from PyQt6.QtCore import QThread, pyqtSignal
from utils.config import get_model

class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, messages, system_prompt=None):
        super().__init__()
        self.messages = messages
        self.system_prompt = system_prompt

    def run(self):
        try:
            client = genai.Client()

            contents = [self.to_content(msg) for msg in self.messages]
            response = client.models.generate_content(
                model=get_model(),
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.4
                )
            )

            self.finished.emit(response.text)
            return
            
        except Exception as e:
            print(str(e))
            self.error.emit(str(e))

    def to_content(self, content):
        google_parts = [types.Part.from_text(text=content['parts'])]
        google_content = types.Content(role=content['role'], parts=google_parts)
        return google_content