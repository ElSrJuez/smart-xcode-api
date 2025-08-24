
from flask import Flask

from admin_utils import admin_config
from flask import Flask
import os


app = Flask(__name__)

# Register blueprints
from routes.admin_home import admin_home_bp
app.register_blueprint(admin_home_bp)


# Root route
@app.route("/")
def admin_root():
    return "Admin UI is running."

if __name__ == "__main__":
    host = admin_config.get('app', 'host', str)
    port = admin_config.get('admin.admin_app', 'admin_port', int)
    log_level = admin_config.get('admin.admin_app', 'logging_admin_app_log_level', str).upper()
    debug = log_level == 'DEBUG'
    app.run(host=host, port=int(port), debug=debug, threaded=True)
