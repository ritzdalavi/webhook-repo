from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB Connection
client = MongoClient("mongodb+srv://admin:admin123@cluster0.hlfbgcq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["webhookDB"]
collection = db["events"]

# 🏠 Home route to render index.html
@app.route("/")
def home():
    return render_template("index.html")

# 📥 Webhook endpoint
@app.route("/webhook", methods=["POST"])
def receive_webhook():
    data = request.json
    event = request.headers.get("X-GitHub-Event")

    if event == "push":
        author = data["pusher"]["name"]
        to_branch = data["ref"].split("/")[-1]
        timestamp = datetime.utcnow()

        doc = {
            "author": author,
            "action": "push",
            "from_branch": None,
            "to_branch": to_branch,
            "timestamp": timestamp,
        }
        collection.insert_one(doc)

    elif event == "pull_request":
        pr = data["pull_request"]
        if pr["state"] == "open":
            author = pr["user"]["login"]
            from_branch = pr["head"]["ref"]
            to_branch = pr["base"]["ref"]
            timestamp = pr["created_at"]

            doc = {
                "author": author,
                "action": "pull_request",
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ"),
            }
            collection.insert_one(doc)

    return jsonify({"status": "OK"}), 200

# 📤 UI endpoint to fetch event data
@app.route("/get-events", methods=["GET"])
def get_events():
    events = list(collection.find().sort("timestamp", -1))
    for e in events:
        e["_id"] = str(e["_id"])
        e["timestamp"] = e["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")
    return jsonify(events)

# 🔁 Start the Flask server
if __name__ == "__main__":
    app.run(debug=True)
