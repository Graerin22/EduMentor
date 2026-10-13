# EduMentor - AI Teaching Assistant

A desktop application that turns any study session into an interactive AI-powered learning.

---

## Project Description

**EduMentor** is a Python desktop application built with PyQt6 that lets students chat with an AI tutor, generate custom multiple-choice quizzes from whatever they're studying, and track every session in their history.

**The problem it addresses:** Students often study by passively reading notes, highlighting, re-reading. Research shows that *active recall* (quizzing yourself) produces far better retention than passive review, but writing your own quiz questions is tedious and most students skip it. EduMentor automates the whole loop: talk to the AI about a topic or upload a document, then let the AI generate a quiz on that material.

**Why it's different:** The system does **not** require a document to be useful. A student can open the app, type "I want to learn recursion," and the AI will ask follow-up questions to figure out their level and goal. Only then does it explain. Quizzes are built from whatever context exists like the uploaded document, the conversation, or both, so the tool is useful from the very first message.

---

## Project Objectives

1. To provide a study tool that keeps the student's documents and history on their own machine.
2. To convert static study material into active-recall practice.
3. To offer per-question AI feedback that adapts to the student's stated confidence level.
4. To track progress across multiple study sessions so students can revisit past quizzes.
5. To keep API keys and passwords encrypted at rest, never stored in plaintext.
6. To demonstrate a clean separation of concerns between GUI, business logic, and persistence.

---

## Features

| Feature | Description |
|---|---|
| **User Accounts** | Register and log in locally. Passwords are SHA-256 hashed with a per-user salt. |
| **Encrypted API Key** | The Gemini API key is encrypted with a key derived from the user's password (Fernet / AES-128). It can only be decrypted by re-entering the correct password. |
| **Chat-First AI Tutor** | Ask anything without uploading a document. The AI asks focused follow-up questions to identify topic, level, and goal before it explains. |
| **Grounded Answers (when a document exists)** | Once a document is uploaded, answers are restricted to its contents. If the answer isn't in the document, the AI says so. |
| **Quiz Generator** | Generate 1–20 multiple-choice questions from the current session - document, chat, or both. Each question has a confidence slider (1–5) so the AI can calibrate its feedback tone. |
| **Per-Question Feedback** | After every submitted answer, the AI explains the correct choice and addresses the student's stated confidence (e.g. high-confidence wrong answers get more detail). |
| **Blind Spot Report** | After finishing a quiz, the AI analyzes the wrong answers and produces a study plan with concrete action steps and resource recommendations. |
| **Session History** | Tree view of every session with its chat and quizzes. Load any past item with a double-click. |
| **Rename / Delete** | Any session, chat, or quiz can be renamed or deleted from the History tab. |
| **Settings** | Change username, password, API key; test a key before saving; delete the account. |

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
│       ├── login_widget.py      # Login tab
│       ├── register_widget.py   # Register tab
│       ├── chat_widget.py       # Mentor tab
│       ├── quiz_widget.py       # Quiz tab
│       ├── history_widget.py    # History tab
│       └── settings_widget.py   # Settings tab
│
├── models/
│   ├── user.py                  # User dataclass
│   └── session.py               # Session, ChatData, QuizData
│
├── ui_designs/
│   ├── login_widget.ui
│   ├── register_widget1.ui
│   ├── register_widget2.ui
│   ├── chat_widget.ui
│   ├── quiz_widget.ui
│   ├── question_widget.ui       # Question slides (loaded N times)
│   ├── history_widget.ui
│   └── settings_widget.ui
│
└── utils/
    ├── config.py                # Path helpers
    └── sliding_stack.py         # SlidingStackedWidget - animated page transitions
```

### Purpose of each major file

| File | Responsibility |
|---|---|
| `EduMentor.py` | Boots the Qt app, instantiates `Database`, opens the login window. |
| `core/database.py` | Owns the SQLite connection; implements every Create/Read/Update/Delete operation and password/API-key cryptography. |
| `core/ai_engine.py` | `AIWorker(QThread)` - takes a message list, calls the model, emits `finished(str)` or `error(str)`. |
| `core/quiz_generator.py` | `QuizWorker(QThread)` - like `AIWorker` but the system prompt forces strict JSON output. |
| `core/document_parser.py` | `DocumentParser(QThread)` - dispatches to the right extractor based on file extension. |
| `gui/main/main_window.py` | Central hub: holds all widgets, connects signals between them, relays logout. |
| `models/session.py` | Data classes shared between DB and widgets - the objects passed around everywhere. |
| `utils/sliding_stack.py` | Custom `QStackedWidget` that animates transitions between quiz slides. |

---

## Installation and Setup

### 1. Prerequisites

- Python **3.10 or newer**
- pip
- A Google Gemini API key - free tier available at <https://aistudio.google.com/app/apikey>

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

### Basic flow (no document needed)

1. **Ask a question** - On the *Mentor* tab, type e.g. *"I want to learn recursion."* Press Send.
2. **Answer the AI's follow-ups** - The AI asks about your level, your goal, and any specifics. Reply naturally.
3. **Learn** - Once intent is clear, the AI explains the topic.
4. **Save the session** - Click **Save**. This creates a session record with your chat history.
5. **Quiz yourself** - Go to the *Quiz* tab, choose a question count (1–20), click **Generate**. The quiz is built from the conversation.
6. **Answer each question** - Pick an option, set your confidence with the slider, submit. Feedback appears under the question.
7. **Get a study plan** - After the last question, click **Blind Spot Report**. The AI identifies weak areas and suggests resources.
8. **Revisit anything** - Open the *History* tab. Double-click any session, chat, or quiz to reload it.
9. **Manage your account** - The *Settings* tab lets you rename yourself, change your password, rotate your API key, or delete the account.

### If you also want to upload a document

1. On the *Mentor* tab, click **Upload** and choose a PDF, DOCX, PPTX, or CSV.
2. The extracted text appears in the left pane. From this point on, the AI answers strictly from the document.
3. Quizzes generated afterwards will be based on **both** the recent document and the recent conversation, giving you questions that cover areas you might not have asked about.

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
| `Session` | `models/session.py` | Aggregate root - holds one `ChatData`, and a list of `QuizData`. |
| `ChatData`, `QuizData` | `models/session.py` | Data classes for each kind of record. |
| `AIWorker`, `QuizWorker`, `DocumentParser` | `core/` | `QThread` subclasses - each runs one long task off the UI thread and reports via Qt signals. |
| `ChatWidget`, `QuizWidget`, `HistoryWidget`, `SettingsWidget` | `gui/pages/` | Each is a `QWidget` subclass responsible for one tab. |
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
- Data classes (`ChatData`, `QuizData`) are plain Python classes used uniformly wherever records move between the DB and the UI.

### Polymorphism

- `MainWindow.on_session_load_requested(session, tab_key, item_idx)` calls `load_session(session, item_idx)` on each of `ChatWidget` and `QuizWidget` without knowing which type it's calling. Each widget implements its own version of that method for its own record type.
- `HistoryWidget.request_load_selected` branches on `isinstance(self.selected_item, ...)` to decide which record to load - the same generic tree item can carry a `Session`, `ChatData`, or a `QuizData`, and the *behaviour* differs based on the object type, not the code path.
- `AIWorker` and `QuizWorker` share the same `finished` / `error` signal interface, so widget code that connects to them is identical regardless of which worker is running.

---

## Database

The application uses a single SQLite file (`sessions.db`) with four tables.

## Schema

### Table: `user`
Stores one row per registered account. Passwords are salted and hashed; the API key is encrypted with a key derived from the password hash and salt.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `user_id` | INTEGER | PK, AUTOINCREMENT | Surrogate primary key. |
| `username` | TEXT | UNIQUE, NOT NULL | Display name and login name. |
| `password_hash` | TEXT | NOT NULL | SHA-256 of `password + salt`, hex-encoded. |
| `salt` | TEXT | NOT NULL | 16-byte random salt, hex-encoded. |
| `encrypted_api_key` | TEXT | NULLABLE | Fernet-encrypted Gemini API key. |
| `created_at` | TEXT | NULLABLE | Human-readable date string when the account was created. |
| `last_login` | TEXT | NULLABLE | Updated on every successful login. |

### Table: `session`
Represents one study session - the top-level container for one chat and any number of quizzes.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `session_id` | INTEGER | PK, AUTOINCREMENT | Surrogate primary key. |
| `user_id` | INTEGER | FK → `user(user_id)`, NOT NULL, CASCADE | Owning account. |
| `timestamp` | TEXT | NULLABLE | Human-readable last-modified string (e.g. `October 13, 2026 at 03:42 PM`). |
| `session_name` | TEXT | UNIQUE, NOT NULL | Auto-generated name (`session_YYYY-MM-DD_HHMMSS`). |
| `is_current` | INTEGER | CHECK IN (0, 1), DEFAULT 0 | Marks the active session for the logged-in user. |

### Table: `chat_data`
The conversation attached to a session. Exactly one per session (enforced by the `1:1` relationship logic in the DB layer).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `chat_id` | INTEGER | PK, AUTOINCREMENT | Surrogate primary key. |
| `session_id` | INTEGER | FK → `session(session_id)`, NOT NULL, CASCADE | Parent session. |
| `timestamp` | TEXT | NULLABLE | Human-readable last-modified string. |
| `chat_name` | TEXT | UNIQUE, NOT NULL | Auto-generated (`chat_<stem>-<HHMMSS>`); stem is `no-doc` when no file was uploaded. |
| `filename` | TEXT | NULLABLE | Original uploaded filename, or NULL if no document was uploaded. |
| `document_text` | TEXT | NULLABLE | Extracted document text, or NULL if no document was uploaded. |
| `chats` | TEXT | NOT NULL | JSON array of `{role, parts}` turns - the full conversation. |

### Table: `quiz_data`
Zero or more quizzes per session. Each row stores the full interaction log for one quiz attempt, including the question set, the user's answers, the per-question feedback, and the score.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `quiz_id` | INTEGER | PK, AUTOINCREMENT | Surrogate primary key. |
| `session_id` | INTEGER | FK → `session(session_id)`, NOT NULL, CASCADE | Parent session. |
| `timestamp` | TEXT | NULLABLE | Human-readable creation/last-modified string. |
| `quiz_name` | TEXT | UNIQUE, NOT NULL | Auto-generated (`quiz_YYYY-MM-DD_HHMMSS`). |
| `quiz_score` | INTEGER | NULLABLE | Number of correct answers so far. |
| `quiz` | TEXT | NOT NULL | JSON array of `{role, parts}` turns - the full AI conversation that produced and graded the quiz. |
| `quiz_result` | TEXT | NOT NULL | JSON array of `{ "No.N": [chosen_answer, "Correct"\|"Wrong"] }` entries, one per answered question. |
| `feedbacks` | TEXT | NOT NULL | JSON array of per-question AI feedback strings. |

### Relationships

- One **user** → many **sessions**.
- One **session** → one **chat_data**, many **quiz_data**.
- Deleting a session cascades to its chat and quizzes.

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
| **Read all sessions** | `get_all_sessions` | History tab |
| **Mark active session** | `set_current_session` | Save, history load |
| **Rename any record** | `rename_session`, `rename_chat_data`, `rename_quiz_data` | History tab |
| **Delete any record** | `delete_session`, `delete_chat_data`, `delete_quiz_data` | History tab |

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

### 4. History Tab
`screenshots/05_history_tab.png`
*The session tree. Sessions expand into chat and quizzes. Any item can be loaded, renamed, or deleted.*

### 5. Settings Tab
`screenshots/06_settings_tab.png`
*Account management: username, password, API key testing, and account deletion.*

---

## Testing

### Manual test cases

| # | Test | Steps | Expected Result | Actual Result |
|---|---|---|---|---|
| 1 | Register a new user | Login → Register → fill form → submit | Account created, login to Mentor tab | Pass |
| 2 | Reject duplicate username | Register with an existing username | Warning: "Username already exists." | Pass |
| 3 | Wrong password | Log in with incorrect password | Warning: "Incorrect password." | Pass |
| 4 | Upload a PDF | Mentor tab → Upload → select a PDF | Extracted text appears; Send enabled | Pass |
| 5 | Ask a question | Type a question → Send | AI response grounded in the document | Pass |
| 6 | Save chat | Click Save | Session row added; message shown | Pass |
| 7 | Generate a quiz | Quiz tab → 5 questions → Generate | 5 question slides appear | Pass |
| 8 | Submit a wrong answer | Select wrong option → Submit | Feedback shows correct explanation | Pass |
| 9 | Blind Spot Report | Finish quiz → Blind Spot Report | Structured study plan appears | Pass |
| 10 | Load a past quiz | History → double-click a quiz | Quiz reloads into Quiz tab | Pass |
| 11 | Rename a session | History → select → Rename | Name updates in DB and tree | Pass |
| 12 | Delete a session | History → select → Delete → Yes | Row + children removed from DB | Pass |
| 13 | Wrong API key | Settings → Test Key with a bad key | Status shows "❌ Invalid key!" | Pass |
| 14 | Correct API key | Settings → Test Key with a valid key | Status shows "✅ Key is valid!" | Pass |
| 15 | Persistence across restart | Close app, reopen, log in | History shows all prior sessions | Pass |

## Known Issues / Limitations
- **`save_quiz_session` require an existing current session.** A quiz cannot be saved before a chat session exists. A future version should auto-create a session on first save.
- **No cloud sync.** Sessions and API keys live only on the local machine.
- **SQLite concurrency.** If the app is opened twice from the same directory, the second instance can lock the DB during writes. A lock file or a single-instance guard is not yet implemented.
- **No image extraction.** PDFs containing scanned images (no text layer) parse as empty. OCR is not implemented.
- **AI responses are non-deterministic.** The same prompt can produce different wording across runs.
- **Quiz JSON parsing can fail** if the model returns prose around the JSON. `QuizWorker` reduces this by enforcing a strict prompt, but a retry mechanism is not yet in place.
- **No password recovery.** Because the API key is encrypted with the password, a forgotten password means the API key cannot be recovered the account must be deleted and re-created.
- **UI files are loaded at runtime with `uic.loadUi`.** Packaging with `pyinstaller` will require bundling the `ui_designs/` folder.

---

## Author

- **Name:** *Niño Rey A. Gealon*
- **Section:** *CS26 (3581)*