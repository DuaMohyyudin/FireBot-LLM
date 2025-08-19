# FireBot-LLM

🔥 **FireBot-LLM** is a full-featured chatbot backend that leverages **Firestore** for persistent user sessions and **Ollama LLM** for generating context-aware, intelligent responses. It is ideal for building advanced chatbots, customer support AI, or any interactive assistant requiring session tracking and conversation memory.

---

## Features

- **User Management**
  - Login via email.
  - Automatic user creation for new emails.
  - Username extraction from email for Firestore indexing.

- **Session Management**
  - Create new chat sessions with unique UUIDs.
  - List all sessions for a user.
  - Retrieve session messages for context continuity.

- **Real-time Chat**
  - Integrates with **Ollama LLM** to generate AI responses.
  - Maintains conversation history per session.
  - Stores both user and assistant messages in Firestore.

- **Per-User History**
  - Optional endpoints to track overall user and agent history.
  - Allows aggregating knowledge for personalized interactions.

- **Tech Stack**
  - Python, Flask, Flask-CORS
  - Firebase Firestore
  - Ollama LLM
  - Requests (for CLI-based testing)

- **Environment Variables**
  - `FIREBASE_KEY_PATH` → path to Firebase service key (default: `firebase-key.json`)
  - `OLLAMA_MODEL` → Ollama model to use (default: `llama3`)

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/FireBot-LLM.git
cd FireBot-LLM

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Firebase key
export FIREBASE_KEY_PATH="path/to/firebase-key.json"

# 5. Pull Ollama model (if not already pulled)
ollama pull llama3
