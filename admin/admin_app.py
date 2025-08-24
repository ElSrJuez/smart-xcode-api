


from flask import Flask, redirect, url_for


from admin.admin_utils import admin_config
from flask import Flask
import os

from flask_admin import Admin, BaseView, expose
from admin.admin_utils import admin_dbops


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))


# Register blueprints
from admin.routes.admin_home import admin_home_bp
app.register_blueprint(admin_home_bp)

from admin.routes.maintenance import maintenance_bp
app.register_blueprint(maintenance_bp)

from admin.routes.category import category_bp
app.register_blueprint(category_bp)

# Flask-Admin setup
admin = Admin(app, name="SmartX Admin", template_mode="bootstrap4")

# Hierarchy View
class HierarchyView(BaseView):
    @expose('/')
    def index(self):
        hierarchy = admin_dbops.get_full_hierarchy()
        get_category_fields = admin_dbops.get_category_fields
        return self.render('admin/hierarchy.html', hierarchy=hierarchy, get_category_fields=get_category_fields)

admin.add_view(HierarchyView(name="Hierarchy", endpoint="hierarchy"))

# Example custom view (replace with TinyDB model view as needed)
class HelloView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/hello.html', message="Welcome to Flask-Admin!")

admin.add_view(HelloView(name="Hello"))



# Root route: redirect to Flask-Admin UI
@app.route("/")
def admin_root():
    return redirect(url_for('admin.index'))

if __name__ == "__main__":
    host = admin_config.get('app', 'host', str)
    port = admin_config.get('admin.admin_app', 'admin_port', int)
    log_level = admin_config.get('admin.admin_app', 'logging_admin_app_log_level', str).upper()
    debug = log_level == 'DEBUG'
    app.run(host=host, port=int(port), debug=debug, threaded=True)
