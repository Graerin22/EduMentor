# EduMentor — AI Teaching Assistant

A desktop application that turns any study document into an interactive AI-powered learning session.

---

## Project Description

**EduMentor** is a Python desktop application built with PyQt6 that lets students upload a study document (PDF, DOCX, PPTX, or CSV), chat with an AI tutor about its contents, generate custom multiple-choice quizzes, and practice explaining concepts back to the AI using the Feynman Technique.

**The problem it addresses:** Students often study by passively reading notes, highlighting, re-reading. Research shows that *active recall* (quizzing yourself) and *self-explanation* (teaching the material back) produce far better retention than passive review, but building quizzes and finding someone to explain to are both time-consuming. EduMentor automates both: it reads the student's own material and generates quizzes and feedback on demand, so active study becomes the default rather than an extra step.

**Why it's different:** Everything is grounded in the student's *own* document. The AI tutor only answers based on the uploaded source, quizzes only cover that material, and teach-back feedback checks the student's explanation against the same source. No hallucinated content from unrelated topics.

---

## Project Objectives

1. Provide a study tool that keeps the student's documents and history on their own machine.
2. Convert static study material into active-recall practice (quizzes, teach-back).
3. Offer per-question AI feedback that adapts to the student's stated confidence level.
4. Track progress across multiple study sessions so students can revisit past quizzes and teach-backs.
5. Keep API keys and passwords encrypted at rest — never stored in plaintext.
6. Demonstrate a clean separation of concerns between GUI, business logic, and persistence.

---

## Features

| Feature | Description |
|---|---|
| **Document Upload** | Load `.pdf`, `.docx`, `.pptx`, or `.csv` files. Text is extracted asynchronously so the UI stays responsive. |
| **AI Chat (Mentor tab)** | Ask questions about the uploaded document. The AI answers only from the document and formats math as plain-text Unicode (no LaTeX). |
| **Quiz Generator** | Generate 1–20 multiple-choice questions from the document. Each question has a confidence slider (1–5) so the AI can calibrate its feedback tone. |
| **Blind Spot Report** | After finishing a quiz, the AI analyzes the wrong answers and produces a study plan with specific resources. |
| **Teach-Back (Feynman)** | Student picks a topic and explains it in their own words. The AI scores clarity, accuracy, and use of analogies, then lists strengths and gaps. |
| **Session History** | Tree view of every session with its chat, quizzes, and teach-backs. Load any past item with a double-click. |
| **Rename / Delete** | Any session, chat, quiz, or teach-back can be renamed or deleted from the History tab. |
| **User Accounts** | Register and log in locally. Passwords are SHA-256 hashed with a per-user salt. |
| **Encrypted API Key** | The Google Gemini API key is encrypted with a key derived from the user's hashed pasword (Fernet / AES-128). It can only be decrypted by re-entering the correct password. |
| **Settings** | Change username, password, API key, test a key before saving, and delete the account. |

---

## Technologies Used

| Category | Choice |
|---|---|
| **Language** | Python 3.10+ |
| **GUI Framework** | PyQt6 (Qt 6) with `.ui` files built in Qt Designer |
| **Database** | SQLite 3 (bundled with Python) |
| **AI Backend** | Google Gemini API (via the `google-generativeai` SDK) |
| **Cryptography** | `cryptography` (Fernet symmetric encryption) |
| **Hashing** | `hashlib` (SHA-256), `secrets` (salt generation, constant-time compare) |
| **Document Parsing** | `pypdf`, `python-docx`, `python-pptx` |
| **Threading** | `QThread` subclasses so AI calls and file parsing never block the UI |
| **Keyring (optional)** | `keyring` for "remember me" auto-login |

### Dependency list

```
PyQt6
cryptography
google-generativeai
pypdf
python-docx
python-pptx
```

---

## Project Structure

```
EduMentor/
├── EduMentor.py                 # Application entry point
├── sessions.db                  # SQLite database
├── requirements.txt             # Dependency list
├── README.md
│
├── core/
│   ├── database.py              # All SQLite operations
│   ├── ai_engine.py             # AIWorker QThread
│   ├── quiz_generator.py        # QuizWorker QThread
│   └── document_parser.py       # DocumentParser QThread
│
│
├── gui/
│   ├── main
│   │   ├── login_window.py      # Login + registration
│   │   └── main_window.py       # QMainWindow with QTabWidget - wires all pages
│   └── pages/
│       ├── chat_widget.py       # Mentor tab
│       ├── quiz_widget.py       # Quiz tab
│       ├── teach_widget.py      # Teach-back tab
│       ├── history_widget.py    # History tab
│       └── settings_widget.py   # Settings tab
│
├── models/
│   ├── user.py                  # User dataclass
│   └── session.py               # Session, ChatData, QuizData, TeachbackData
│
├── ui_designs/
│   ├── login_window.ui
│   ├── chat_widget.ui
│   ├── quiz_widget.ui
│   ├── question_widget.ui       # Question slides (loaded N times)
│   ├── teach_widget.ui
│   ├── history_widget.ui
│   └── settings_widget.ui
│
└── utils/
    ├── config.py                # Path helpers
    └── sliding_stack.py         # SlidingStackedWidget — animated page transitions
```

### Purpose of each major file

| File | Responsibility |
|---|---|
| `main.py` | Boots the Qt app, instantiates `Database`, opens the login window. |
| `core/database.py` | Owns the SQLite connection; implements every Create/Read/Update/Delete operation and password/API-key cryptography. |
| `core/ai_engine.py` | `AIWorker(QThread)` - takes a message list, calls the model, emits `finished(str)` or `error(str)`. |
| `core/quiz_generator.py` | `QuizWorker(QThread)` - like `AIWorker` but the system prompt forces strict JSON output. |
| `core/document_parser.py` | `DocumentParser(QThread)` - dispatches to the right extractor based on file extension. |
| `gui/main_window.py` | Central hub: holds all widgets, connects signals between them, relays logout. |
| `models/session.py` | Data classes shared between DB and widgets — the objects passed around everywhere. |
| `utils/sliding_stack.py` | Custom `QStackedWidget` that animates transitions between quiz slides. |

---

## Installation and Setup

### 1. Prerequisites

- Python **3.10 or newer**
- pip
- A Google Gemini API key — free tier available at <https://aistudio.google.com/app/apikey>

### 2. Clone the repository

```bash
git clone https://github.com/Graerin22/EduMentor
cd EduMentor
```

### 3. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python EduMentor.py
```

The first launch creates `sessions.db` in the project root. No migrations are needed - the schema is applied on startup.

### 6. First-time setup inside the app

1. Click **Register** on the login window.
2. Enter a username, password, and your Gemini API key.
3. Log in. You'll land on the **Mentor** tab.

---

## How to Use the System

### Basic flow

1. **Upload a document** - On the *Mentor* tab, click **Upload** and choose a PDF, DOCX, PPTX, or CSV. The extracted text appears in the left pane.
2. **Ask questions** - Type into the input box and press **Send**. The AI answers strictly from the document.
3. **Save the session** - Click **Save**. This creates a session record with your chat history.
4. **Take a quiz** - Go to the *Quiz* tab, enter a question count (1–20), click **Generate**. Answer each question, set your confidence with the slider, and submit. Feedback appears under the question.
5. **Get a study plan** - After the last question, click **Blind Spot Report**. The AI identifies weak areas and suggests resources.
6. **Practice teach-back** - On the *Teach-back* tab, enter a topic and explain it in your own words. The AI scores it using the Feynman criteria.
7. **Revisit anything** - Open the *History* tab. Double-click any session, chat, quiz, or teach-back to reload it.
8. **Manage your account** - The *Settings* tab lets you rename yourself, change your password, rotate your API key, or delete the account.

### Keyboard / UI shortcuts

| Action | Where |
|---|---|
| Double-click a tree item | Load it into the corresponding tab |
| Confidence slider | Drag before submitting each quiz answer |
| Enter in the chat input | Sends the message |

---

## OOP Implementation

### Core classes

| Class | File | Role |
|---|---|---|
| `Database` | `core/database.py` | Data-access layer. Every SQL statement lives here. |
| `User` | `models/user.py` | Value object for the authenticated user. |
| `Session` | `models/session.py` | Aggregate root - holds one `ChatData`, a list of `QuizData`, and a list of `TeachbackData`. |
| `ChatData`, `QuizData`, `TeachbackData` | `models/session.py` | Data classes for each kind of record. |
| `AIWorker`, `QuizWorker`, `DocumentParser` | `core/` | `QThread` subclasses - each runs one long task off the UI thread and reports via Qt signals. |
| `ChatWidget`, `QuizWidget`, `TeachWidget`, `HistoryWidget`, `SettingsWidget` | `gui/pages/` | Each is a `QWidget` subclass responsible for one tab. |
| `MainWindow` | `gui/main_window.py` | `QMainWindow` subclass that composes the tabs and relays events. |
| `SlidingStackedWidget` | `utils/sliding_stack.py` | `QStackedWidget` subclass adding animated transitions. |

### Encapsulation

- All database access is behind `Database` methods. No widget ever touches `sqlite3` directly - the widget calls `self.db.save_chat_session(...)`, never `cursor.execute(...)`.
- The API key never appears as plaintext in the database. `Database._encrypt_api_key` and `_decrypt_api_key` are private (underscore-prefixed) - only `register_user`, `authenticate_user`, and `change_api_key` can trigger them.
- Passwords are hashed, not stored. `_hash_password` and `_verify_password` are also private; the widget only sees `(success, message)` tuples.
- Each `Widget` keeps its runtime state (`self.quiz_data`, etc.) private to the tab - no widget reads another widget's attributes.

### Inheritance

- Every GUI class extends `QWidget` or `QMainWindow`, inheriting the entire Qt event system, layout machinery, and signal/slot framework.
- `AIWorker`, `QuizWorker`, and `DocumentParser` all extend `QThread`, inheriting `start()`, `finished`, `error`, and the run-loop integration.
- `SlidingStackedWidget` extends `QStackedWidget`, adding animation on top of the standard page-switching behaviour.
- Data classes (`ChatData`, `QuizData`, `TeachbackData`) are plain Python classes used uniformly wherever records move between the DB and the UI.

### Polymorphism

- `MainWindow.on_session_load_requested(session, tab_key, item_idx)` calls `load_session(session, item_idx)` on each of `ChatWidget`, `QuizWidget`, and `TeachWidget` without knowing which type it's calling. Each widget implements its own version of that method for its own record type.
- `HistoryWidget.request_load_selected` branches on `isinstance(self.selected_item, ...)` to decide which record to load - the same generic tree item can carry a `Session`, `ChatData`, `QuizData`, or `TeachbackData`, and the *behaviour* differs based on the object type, not the code path.
- `AIWorker` and `QuizWorker` share the same `finished` / `error` signal interface, so widget code that connects to them is identical regardless of which worker is running.

---

## Database

The application uses a single SQLite file (`sessions.db`) with five tables.

### Schema

```
user
├── user_id           INTEGER  PK
├── username          TEXT     UNIQUE
├── password_hash     TEXT
├── salt              TEXT
├── encrypted_api_key TEXT
├── created_at        TEXT
└── last_login        TEXT

session
├── session_id        INTEGER  PK
├── user_id           INTEGER  FK → user(user_id) ON DELETE CASCADE
├── timestamp         TEXT
├── session_name      TEXT     UNIQUE
└── is_current        INTEGER  0/1

chat_data
├── chat_id           INTEGER  PK
├── session_id        INTEGER  FK → session(session_id) ON DELETE CASCADE
├── timestamp         TEXT
├── chat_name         TEXT     UNIQUE
├── filename          TEXT
├── document_text     TEXT
└── chats             TEXT     (JSON array)

quiz_data
├── quiz_id           INTEGER  PK
├── session_id        INTEGER  FK → session(session_id) ON DELETE CASCADE
├── timestamp         TEXT
├── quiz_name         TEXT     UNIQUE
├── quiz_score        INTEGER
├── quiz              TEXT     (JSON array of chat turns)
├── quiz_result       TEXT
└── feedbacks         TEXT 

teachback_data
├── teachback_id      INTEGER  PK
├── session_id        INTEGER  FK → session(session_id) ON DELETE CASCADE
├── timestamp         TEXT
├── teachback_name    TEXT     UNIQUE
├── topic             TEXT
├── explanation       TEXT
└── teachback         TEXT     (JSON array of chat turns)
```

### Relationships

- One **user** → many **sessions**.
- One **session** → one **chat_data**, many **quiz_data**, many **teachback_data**.
- Deleting a session cascades to its chat, quizzes, and teach-backs.

### Major database operations

| Operation | Method(s) | Called from |
|---|---|---|
| **Create user** | `register_user` | Login window |
| **Read user** | `authenticate_user` | Login window |
| **Update user** | `change_username`, `change_password`, `change_api_key` | Settings tab |
| **Delete user** | `delete_account` | Settings tab |
| **Create session + chat** | `save_chat_session` | Mentor tab |
| **Update chat** | `update_chat_session` | Mentor tab |
| **Create quiz** | `save_quiz_session` | Quiz tab |
| **Update quiz** | `update_quiz_session` | Quiz tab |
| **Create teach-back** | `save_teachback_session` | Teach-back tab |
| **Update teach-back** | `update_teachback_session` | Teach-back tab |
| **Read all sessions** | `get_all_sessions` | History tab |
| **Mark active session** | `set_current_session` | Save, history load |
| **Rename any record** | `rename_session`, `rename_chat_data`, `rename_quiz_data`, `rename_teachback_data` | History tab |
| **Delete any record** | `delete_session`, `delete_chat_data`, `delete_quiz_data`, `delete_teachback_data` | History tab |

---

## Screenshots

### 1. Login Window
`screenshots/01_login.png`
*The login and registration window. Users create an account with a username, password, and Gemini API key.*

### 2. Mentor Tab
`screenshots/02_mentor_tab.png`
*The Mentor tab after uploading a PDF. The left pane shows the extracted document text; the right pane shows the AI conversation.*

### 3. Quiz Tab
`screenshots/03_quiz_tab.png`
*One multiple-choice question with the confidence slider. The progress and score labels update in real time.*

### 4. Teach-Back Tab
`screenshots/04_teachback_tab.png`
*The Feynman-technique evaluation, with scores for clarity, accuracy, and analogies.*

### 5. History Tab
`screenshots/05_history_tab.png`
*The session tree. Sessions expand into chat, quizzes, and teach-backs. Any item can be loaded, renamed, or deleted.*

### 6. Settings Tab
`screenshots/06_settings_tab.png`
*Account management: username, password, API key testing, and account deletion.*

---

## Testing

### Manual test cases

| # | Test | Steps | Expected Result | Actual Result |
|---|---|---|---|---|
| 1 | Register a new user | Login → Register → fill form → submit | Account created, auto-login to Mentor tab | Pass |
| 2 | Reject duplicate username | Register with an existing username | Warning: "Username already exists." | Pass |
| 3 | Wrong password | Log in with incorrect password | Warning: "Incorrect password." | Pass |
| 4 | Upload a PDF | Mentor tab → Upload → select a PDF | Extracted text appears; Send enabled | Pass |
| 5 | Ask a question | Type a question → Send | AI response grounded in the document | Pass |
| 6 | Save chat | Click Save | Session row added; message shown | Pass |
| 7 | Generate a quiz | Quiz tab → 5 questions → Generate | 5 question slides appear | Pass |
| 8 | Submit a wrong answer | Select wrong option → Submit | Feedback shows ❌ and correct explanation | Pass |
| 9 | Blind Spot Report | Finish quiz → Blind Spot Report | Structured study plan appears | Pass |
| 10 | Teach-back | Enter topic + explanation → Submit | Scores + strengths + gaps shown | Pass |
| 11 | Load a past quiz | History → double-click a quiz | Quiz reloads into Quiz tab | Pass |
| 12 | Rename a session | History → select → Rename | Name updates in DB and tree | Pass |
| 13 | Delete a session | History → select → Delete → Yes | Row + children removed from DB | Pass |
| 14 | Wrong API key | Settings → Test Key with a bad key | Status shows "❌ Invalid key!" | Pass |
| 15 | Correct API key | Settings → Test Key with a valid key | Status shows "✅ Key is valid!" | Pass |
| 16 | Persistence across restart | Close app, reopen, log in | History shows all prior sessions | Pass |

## Known Issues / Limitations
- **`save_quiz_session` / `save_teachback_session` require an existing current session.** A quiz cannot be saved before a chat session exists. A future version should auto-create a session on first save.
- **No cloud sync.** Sessions and API keys live only on the local machine.
- **SQLite concurrency.** If the app is opened twice from the same directory, the second instance can lock the DB during writes. A lock file or a single-instance guard is not yet implemented.
- **No image extraction.** PDFs containing scanned images (no text layer) parse as empty. OCR is not implemented.
- **AI responses are non-deterministic.** The same prompt can produce different wording across runs; the tests in `tests/` therefore validate structure, not exact strings.
- **Quiz JSON parsing can fail** if the model returns prose around the JSON. `QuizWorker` reduces this by enforcing a strict prompt, but a retry mechanism is not yet in place.
- **No password recovery.** Because the API key is encrypted with the password, a forgotten password means the API key cannot be recovered the account must be deleted and re-created.
- **Auto-login (keyring) is optional and off by default.** A checkbox in the login window is planned but not yet implemented.
- **UI files are loaded at runtime with `uic.loadUi`.** Packaging with `pyinstaller` will require bundling the `ui_designs/` folder.

---

## Author

- **Name:** *Niño Rey A. Gealon*
- **Section:** *CS26 (3581)*
