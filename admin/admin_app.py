

from flask import Flask
from utils.config import ADMIN_PORT, GLOBAL_HOST
from utils.logging import log_message

app = Flask(__name__)

@app.route("/")
def admin_home():
    log_message('info', "Admin endpoint accessed.")
    return "Admin endpoint: Secure access only."

if __name__ == "__main__":
    debug = ADMIN_LOGGING == 'DEBUG'
    app.run(host=GLOBAL_HOST, port=ADMIN_PORT, debug=debug, threaded=True)
