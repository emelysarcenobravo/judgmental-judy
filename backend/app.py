import os
import secrets

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

load_dotenv()  # before importing db, which reads DATABASE_URL

from auth import auth  # noqa: E402
from budget import budget  # noqa: E402
from db import init_db  # noqa: E402
from judy.chat import judy  # noqa: E402

app = Flask(__name__)
# Signs the login cookie. Without SECRET_KEY in .env, everyone is logged out on each restart.
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Deployed sites use https, so only send the login cookie over https there.
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true",
)
CORS(app)

init_db(app)
app.register_blueprint(auth)
app.register_blueprint(budget)
app.register_blueprint(judy)  # Judy's chat lives in judy/chat.py


@app.route("/")
def index():
    return {"message": "Judgmental Judy API. Try /api/health"}


@app.route("/api/health")
def health():
    return {"status": "Judy is watching your spending"}


if __name__ == "__main__":
    app.run(debug=True, port=5001)