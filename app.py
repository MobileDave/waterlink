from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/elevenlabs-webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received webhook:", data)
    # Add your logic here to process the webhook data
    return jsonify({"status": "success"}), 200

@app.route('/', methods=['GET'])
def home():
    return "Webhook is running!", 200
