from flask import Flask
from flask_cors import CORS

from auth_blueprint import authentication_blueprint
from users_blueprint import users_blueprint
from reports_blueprint import reports_blueprint
from comments_blueprint import comments_blueprint
from ai_blueprint import ai_blueprint
from geocoding_blueprint import geocoding_blueprint

app = Flask(__name__)

CORS(app, resources={
     r"/*": {"origins": ["http://localhost:5173", "https://hydrowave.netlify.app"]}}, supports_credentials=True)

app.register_blueprint(authentication_blueprint)
app.register_blueprint(users_blueprint)
app.register_blueprint(reports_blueprint)
app.register_blueprint(comments_blueprint)
app.register_blueprint(ai_blueprint)
app.register_blueprint(geocoding_blueprint)


if __name__ == '__main__':
    app.run(port=5000)