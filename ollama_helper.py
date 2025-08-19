import ollama

def chat_with_ollama(model: str, history: list, user_message: str) -> tuple[list, str]:
    """
    Sends conversation history + new user message to Ollama and returns
    updated history with assistant reply.
    """

    # Append user input
    history.append({"role": "user", "content": user_message})

    # Query Ollama
    response = ollama.chat(model=model, messages=history)
    agent_reply = response["message"]["content"]

    # Append Ollama response
    history.append({"role": "assistant", "content": agent_reply})

    return history, agent_reply
