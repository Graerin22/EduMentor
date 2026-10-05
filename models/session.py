from dataclasses import dataclass, field

@dataclass
class Session:
    session_id:int
    user_id:int
    timestamp: str
    session_name: str
    chat_data: ChatData
    is_current: bool = False
    quiz_datas: list[QuizData] = field(default_factory=list)
    teachback_datas: list[TeachbackData] = field(default_factory=list)

@dataclass
class ChatData:
    chat_id: int
    session_id: int
    timestamp: str
    chat_name: str
    filename: str
    document_text: str
    chats: list[dict] = field(default_factory=list)

    def chat_length(self):
        return len(self.chats)

@dataclass
class QuizData:
    quiz_id: int
    session_id: int
    timestamp: str
    quiz_name: str
    quiz_score: int
    quiz: list[dict] = field(default_factory=list)
    quiz_result: list = field(default_factory=list)
    feedbacks: list = field(default_factory=list)

    def quiz_length(self):
        return len(self.quiz)

@dataclass
class TeachbackData:
    teachback_id: int
    session_id: int
    timestamp: str
    teachback_name: str
    topic: str
    explanation: str
    teachback: list[dict] = field(default_factory=list)