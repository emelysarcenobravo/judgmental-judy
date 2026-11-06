import os
import secrets

import anthropic
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS

load_dotenv()  # before importing db, which reads DATABASE_URL

from auth import auth  # noqa: E402
from db import init_db  # noqa: E402

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

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from .env

JUDY_PROMPT = """You are Judgmental Judy, a witty, sarcastic AI budget advisor.
You help users understand their spending and make better choices.
The less discretionary money they have left, the more judgmental you get.
Keep the roasting playful, never cruel, and always end with a useful tip.
Keep replies short: 2-4 sentences."""


@app.route("/")
def index():
    return {"message": "Judgmental Judy API. Try /api/health"}


@app.route("/api/health")
def health():
    return {"status": "Judy is watching your spending"}


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")  # [{"role": "user" | "assistant", "content": "..."}]
    budget = data.get("budget")      # optional summary, e.g. {"remaining": 42, "spent": 358}

    if not messages:
        return {"error": "messages is required"}, 400
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"error": "Add ANTHROPIC_API_KEY to backend/.env"}, 500

    system = JUDY_PROMPT
    if budget:
        system += f"\n\nThe user's current budget: {budget}"

    try:
        response = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=16000,
            system=system,
            messages=messages,
            output_config={"effort": "low"},
        )
    except anthropic.AuthenticationError:
        return {"error": "Invalid or missing ANTHROPIC_API_KEY"}, 500
    except anthropic.RateLimitError:
        return {"error": "Judy needs a breather. Try again in a moment."}, 429
    except anthropic.APIStatusError as e:
        return {"error": e.message}, 502
    except anthropic.APIConnectionError:
        return {"error": "Could not reach the Claude API"}, 502

    if response.stop_reason == "refusal":
        return {"reply": "Even Judy won't touch that one. Ask me about your budget instead."}

    reply = next((b.text for b in response.content if b.type == "text"), "")
    return {"reply": reply}


if __name__ == "__main__":
    app.run(debug=True, port=5001)
