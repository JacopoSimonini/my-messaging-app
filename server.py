import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
# from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
# CORS(app)  # permette richieste da browser/client esterni

# Config database: usa DATABASE_URL da variabile d'ambiente (es. Render PostgreSQL)
db_url = os.environ.get("DATABASE_URL", "sqlite:///messages.db")
# Render fornisce DATABASE_URL con schema "postgres://", ma SQLAlchemy vuole "postgresql://"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    delivered = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)  # data/ora di lettura


@app.route("/send", methods=["POST"])
def send_message():
    data = request.json

    # Validazione semplice
    if not data or not all(k in data for k in ("sender", "receiver", "text")):
        return jsonify({"error": "Missing sender, receiver or text"}), 400

    msg = Message(
        sender=data["sender"],
        receiver=data["receiver"],
        text=data["text"]
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "ok", "message_id": msg.id}), 201


@app.route("/get_messages", methods=["GET"])
def get_messages():
    receiver = request.args.get("receiver")
    if not receiver:
        return jsonify({"error": "Missing receiver parameter"}), 400

    messages = Message.query.filter_by(receiver=receiver, delivered=False).all()
    output = []
    for msg in messages:
        output.append({
            "id": msg.id,
            "sender": msg.sender,
            "text": msg.text,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
        msg.delivered = True
        msg.read_at = datetime.utcnow()  # segna data/ora di lettura

    db.session.commit()
    return jsonify(output)


def delete_old_messages():
    """Cancella i messaggi letti da più di 1 giorno"""
    limit_time = datetime.utcnow() - timedelta(days=1)
    old_msgs = Message.query.filter(
        Message.read_at != None,
        Message.read_at < limit_time
    ).all()

    for msg in old_msgs:
        db.session.delete(msg)

    if old_msgs:
        db.session.commit()
        print(f"Deleted {len(old_msgs)} old messages")


# Scheduler che ogni ora controlla ed elimina vecchi messaggi
scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_old_messages, trigger="interval", hours=1)
scheduler.start()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    # Render assegna la porta tramite variabile d'ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
