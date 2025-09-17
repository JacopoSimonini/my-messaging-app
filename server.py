from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///messages.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    delivered = db.Column(db.Boolean, default=False)


@app.route("/send", methods=["POST"])
def send_message():
    data = request.json
    msg = Message(
        sender=data["sender"],
        receiver=data["receiver"],
        text=data["text"]
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "ok", "message_id": msg.id})


@app.route("/get_messages", methods=["GET"])
def get_messages():
    receiver = request.args.get("receiver")
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
    db.session.commit()
    return jsonify(output)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
