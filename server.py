from flask import Flask, request, jsonify
import os
from threading import Lock

app = Flask(__name__)

# Struttura dati semplice in memoria per messaggi
messages = []
lock = Lock()  # Per accesso thread-safe

@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json()
    sender = data.get("sender")
    receiver = data.get("receiver")
    text = data.get("text")

    if not sender or not receiver or not text:
        return jsonify({"error": "Dati mancanti"}), 400

    # Aggiungi messaggio alla lista
    with lock:
        messages.append({
            "sender": sender,
            "receiver": receiver,
            "text": text
        })
    return jsonify({"status": "ok"}), 200

@app.route("/get_messages", methods=["GET"])
def get_messages():
    receiver = request.args.get("receiver")
    if not receiver:
        return jsonify({"error": "Receiver mancante"}), 400

    # Filtra messaggi per il receiver e li rimuove dalla lista
    with lock:
        user_messages = [m for m in messages if m["receiver"] == receiver]
        messages[:] = [m for m in messages if m["receiver"] != receiver]

    return jsonify(user_messages), 200

if __name__ == "__main__":
    # Render passa la porta tramite variabile d'ambiente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
