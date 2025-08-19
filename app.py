import os
from uuid import uuid4
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

# ============== Flask ==============
app = Flask(__name__)
CORS(app)

# ============== Firebase ==============
# Make sure firebase-key.json is in the same directory, or set path via env var FIREBASE_KEY_PATH
FIREBASE_KEY_PATH = os.environ.get("FIREBASE_KEY_PATH", "firebase-key.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ============== LLM (Ollama) ==============
# pip install ollama  (and have an Ollama model pulled, e.g., `ollama pull llama3`)
import ollama
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")  

def username_from_email(email: str) -> str:
    return email.split("@")[0].strip().lower()

@app.route("/")
def home():
    return jsonify({"message": "🔥 Chatbot Backend with Firestore Running!"})


# -------------------------
# User Login
# -------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400

    uname = username_from_email(email)
    user_ref = db.collection("users").document(uname)
    snap = user_ref.get()

    if not snap.exists:
        new_user = {"email": email, "sessions": []}
        user_ref.set(new_user)
        return jsonify({"message": "New user created", "user": new_user}), 201

    return jsonify({"message": "Login successful", "user": snap.to_dict()}), 200


# -------------------------
# List Sessions
# -------------------------
@app.route("/sessions", methods=["GET"])
def get_sessions():
    email = (request.args.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400

    uname = username_from_email(email)
    user_ref = db.collection("users").document(uname)
    if not user_ref.get().exists:
        return jsonify({"sessions": []}), 200  # no user yet

    # list subcollection docs under users/{uname}/sessions
    sess_ref = user_ref.collection("sessions")
    docs = sess_ref.stream()
    session_ids = [doc.id for doc in docs]

    # (Optional) Keep top-level `sessions` field in sync
    user_ref.set({"sessions": session_ids}, merge=True)

    return jsonify({"sessions": session_ids}), 200


# -------------------------
# Create New Session
# -------------------------
@app.route("/session", methods=["POST"])
def create_session():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400

    uname = username_from_email(email)
    user_ref = db.collection("users").document(uname)
    if not user_ref.get().exists:
        return jsonify({"error": "User not found"}), 404

    session_id = str(uuid4())
    sess_doc = user_ref.collection("sessions").document(session_id)
    sess_doc.set({
        "created_at": firestore.SERVER_TIMESTAMP,
        "messages": []  # each item: {"role": "user"|"assistant", "content": "...", "ts": server_ts}
    })

    # update top-level sessions array (optional)
    user_ref.set({"sessions": firestore.ArrayUnion([session_id])}, merge=True)

    return jsonify({"session_id": session_id}), 201


# -------------------------
# Get Session Messages
# -------------------------
@app.route("/session/<session_id>", methods=["GET"])
def get_session_messages(session_id):
    email = (request.args.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400

    uname = username_from_email(email)
    user_ref = db.collection("users").document(uname)
    sess_doc = user_ref.collection("sessions").document(session_id).get()

    if not sess_doc.exists:
        return jsonify({"error": "Session not found"}), 404

    data = sess_doc.to_dict() or {}
    return jsonify({"messages": data.get("messages", [])}), 200


# -------------------------
# Chat in a session
# -------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip()
    session_id = (data.get("session_id") or "").strip()
    user_msg = (data.get("message") or "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    if not user_msg:
        return jsonify({"error": "message required"}), 400

    uname = username_from_email(email)
    user_ref = db.collection("users").document(uname)
    if not user_ref.get().exists:
        return jsonify({"error": "User not found"}), 404

    sess_doc = user_ref.collection("sessions").document(session_id)
    sess_snap = sess_doc.get()
    if not sess_snap.exists:
        return jsonify({"error": "Session not found"}), 404

    data = sess_snap.to_dict() or {}
    messages = data.get("messages", [])

    # Append the new user message
    messages.append({"role": "user", "content": user_msg})

    # Call Ollama
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        assistant_reply = response["message"]["content"]
    except Exception as e:
        return jsonify({"error": f"Ollama error: {e}"}), 500

    # Append assistant reply and persist
    messages.append({"role": "assistant", "content": assistant_reply})
    sess_doc.update({
        "messages": messages,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "last_reply": assistant_reply
    })

    return jsonify({"reply": assistant_reply}), 200


# -------------------------
# Optional: per-user history
# -------------------------
@app.route("/history/<username>", methods=["GET"])
def get_history(username):
    try:
        user_ref = db.collection("users").document(username).get()
        if not user_ref.exists:
            return jsonify({"error": "User not found"}), 404

        user_data = user_ref.to_dict()
        return jsonify({
            "user": username,
            "agent_history": user_data.get("agent_history", []),
            "user_history": user_data.get("user_history", [])
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history/<username>", methods=["POST"])
def add_history(username):
    try:
        data = request.get_json(force=True) or {}
        user_msg = data.get("user_msg")
        agent_msg = data.get("agent_msg")

        user_ref = db.collection("users").document(username)
        if not user_ref.get().exists:
            return jsonify({"error": "User not found"}), 404

        updates = {}
        if user_msg:
            updates["user_history"] = firestore.ArrayUnion([user_msg])
        if agent_msg:
            updates["agent_history"] = firestore.ArrayUnion([agent_msg])

        if updates:
            user_ref.set(updates, merge=True)

        return jsonify({"message": "History updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============== Run ==============
if __name__ == "__main__":
    app.run(debug=True, port=5000)
