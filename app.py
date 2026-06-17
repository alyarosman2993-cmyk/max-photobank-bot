from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "MAX Photobank Bot работает"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(data)
    return {"status": "ok"}

if __name__ == "__main__":
    app.run()
