from flask import Flask
from flask_cors import CORS
from auth_blueprint import authentication_blueprint
from users_blueprint import users_blueprint
from reports_blueprint import reports_blueprint
from comments_blueprint import comments_blueprint

# Initialize Flask
# We'll use the pre-defined global '__name__' variable to tell Flask where it is.
app = Flask(__name__)

CORS(app)

app.register_blueprint(authentication_blueprint)
app.register_blueprint(users_blueprint)
app.register_blueprint(reports_blueprint)
app.register_blueprint(comments_blueprint)


# Running app in debug mode (for auto-refresh) and setting up port to 5001
if __name__ == '__main__':
    app.run()



