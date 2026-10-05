import json
from google import genai
from google.genai import types
from PySide6.QtCore import QThread, Signal
from utils.config import get_model

class QuizWorker(QThread):
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def run(self):     
        try:
            client = genai.Client()

            contents = [self.to_content(msg) for msg in self.messages]
            response = client.models.generate_content(
                model=get_model(),
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json"
                )
            )

            # raw_text = response.text.strip()
            # if raw_text.startswith("```json"):
            #     raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
            # elif raw_text.startswith("```"):
            #     raw_text = raw_text.split("```")[-1].split("```")[0].strip()

            data = json.loads(response.text)
            self.finished.emit(data['questions'])
            
        except Exception as e:
            self.error.emit(str(e))

    def to_content(self, content):
        google_parts = [types.Part.from_text(text=content['parts'])]
        google_content = types.Content(role=content['role'], parts=google_parts)
        return google_content