import requests

BASE = "http://127.0.0.1:5000"


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"_error_body": resp.text, "_status": resp.status_code}


def main():
    email = input("Enter your email: ").strip()

    # -------- Login --------
    resp = requests.post(f"{BASE}/login", json={"email": email})
    data = safe_json(resp)
    print(data)
    if resp.status_code not in (200, 201):
        print("Login failed. Exiting.")
        return

    # -------- List sessions --------
    resp = requests.get(f"{BASE}/sessions", params={"email": email})
    data = safe_json(resp)
    if resp.status_code != 200:
        print("Failed to fetch sessions:", data)
        return

    sessions = data.get("sessions", [])
    print("\n=== Your Sessions ===")
    if not sessions:
        print("(none)")
    else:
        for i, s in enumerate(sessions, start=1):
            print(f"{i}. {s}")

    # -------- Choose or create session --------
    if sessions:
        choice = input("\nSelect session number or type 'n' for new: ").strip()
    else:
        choice = "n"

    if choice.lower() == "n":
        resp = requests.post(f"{BASE}/session", json={"email": email})
        data = safe_json(resp)
        if resp.status_code != 201:
            print("Failed to create session:", data)
            return
        session_id = data["session_id"]
        print(f"Created new session: {session_id}")
    else:
        try:
            session_id = sessions[int(choice) - 1]
            print(f"Resuming session: {session_id}")

            # 🔹 Fetch previous messages
            resp = requests.get(f"{BASE}/session/{session_id}", params={"email": email})
            data = safe_json(resp)
            if resp.status_code == 200:
                messages = data.get("messages", [])
                if messages:
                    print("\n=== Previous Chat ===")
                    for m in messages:
                        role = "You" if m["role"] == "user" else "Bot"
                        print(f"{role}: {m['content']}")
                    print("=== End of History ===\n")
            else:
                print("No previous messages found.")

        except Exception:
            print("Invalid choice.")
            return

    # -------- Chat loop --------
    print("\n=== Start Chatting (type 'exit' to quit) ===")
    while True:
        user_message = input("\nYou: ")
        if user_message.lower() in ["exit", "quit"]:
            break

        resp = requests.post(
            f"{BASE}/chat",
            json={"email": email, "session_id": session_id, "message": user_message},
        )

        data = safe_json(resp)
        if resp.status_code != 200:
            print("Error:", data)
            continue

        print("Bot:", data.get("reply", ""))


if __name__ == "__main__":
    main()
