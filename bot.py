from flask import Flask
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "🌹 Rose Admin Bot - Web Service is Running!"

@app.route('/health')
def health():
    return "✅ OK", 200

@app.route('/status')
def status():
    return "🤖 Bot Status: Web service running. Check worker service for bot status."

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🚀 Starting web service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
