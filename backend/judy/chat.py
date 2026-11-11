"""POST /api/chat: talk to Judy about your own budget.

The browser sends ONLY the conversation. Every number Judy sees is read from the
database for the logged-in user, so nobody can feed her fake figures.
"""

import os
import time
from collections import defaultdict, deque

import anthropic
from flask import Blueprint, request, session

from auth import login_required
from db import get_db
from judy.context import build_judy_inputs
from judy.persona import build_system_prompt

judy = Blueprint("judy", __name__, url_prefix="/api")

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 1000          # replies are ~100 words; this is just a safety ceiling
MAX_MESSAGES = 20          # most recent turns the browser may send
MAX_MESSAGE_CHARS = 1000

# Simple in-memory rate limit per user. Fine for one gunicorn worker (Render's default);
# with several workers each would count separately.
RATE_LIMIT = 20            # requests...
RATE_WINDOW_SECONDS = 600  # ...per 10 minutes
_recent_requests = defaultdict(deque)

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _client


def rate_limited(user_id):
    now = time.monotonic()
    recent = _recent_requests[user_id]
    while recent and now - recent[0] > RATE_WINDOW_SECONDS:
        recent.popleft()
    if len(recent) >= RATE_LIMIT:
        return True
    recent.append(now)
    return False


def clean_messages(raw):
    """Return (messages, error). Keeps only role and content, and checks the conversation shape."""
    if not isinstance(raw, list) or not raw:
        return None, "messages is required"
    if len(raw) > MAX_MESSAGES:
        return None, f"Too many messages (max {MAX_MESSAGES})"
    messages = []
    for m in raw:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            return None, "Each message needs a role of user or assistant"
        content = m.get("content")
        if not isinstance(content, str) or not content.strip():
            return None, "Each message needs text content"
        if len(content) > MAX_MESSAGE_CHARS:
            return None, f"Keep each message under {MAX_MESSAGE_CHARS} characters"
        messages.append({"role": m["role"], "content": content.strip()})
    if messages[0]["role"] != "user" or messages[-1]["role"] != "user":
        return None, "The conversation must start and end with a user message"
    return messages, None


@judy.post("/chat")
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    messages, error = clean_messages(data.get("messages"))
    if error:
        return {"error": error}, 400

    user_id = session["user_id"]
    try:
        profile, summary = build_judy_inputs(get_db(), user_id, data.get("month"))
    except ValueError as e:  # bad month format
        return {"error": str(e)}, 400
    if profile is None:
        return {"error": "Set up your budget first so Judy has something to judge"}, 400

    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"error": "Judy isn't connected to Claude yet (missing ANTHROPIC_API_KEY)"}, 500
    if rate_limited(user_id):
        return {"error": "Judy needs a breather. Try again in a few minutes."}, 429

    try:
        response = get_client().messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=build_system_prompt(profile, summary),
            messages=messages,
            output_config={"effort": "low"},
        )
    except anthropic.AuthenticationError:
        return {"error": "Invalid ANTHROPIC_API_KEY"}, 500
    except anthropic.RateLimitError:
        return {"error": "Judy needs a breather. Try again in a moment."}, 429
    except anthropic.APIStatusError as e:
        return {"error": e.message}, 502
    except anthropic.APIConnectionError:
        return {"error": "Could not reach the Claude API"}, 502

    if response.stop_reason == "refusal":
        return {"reply": "Even Judy won't touch that one. Ask me about your budget instead.", "tier": summary["tier"]}

    reply = next((b.text for b in response.content if b.type == "text"), "").strip()
    if not reply:
        return {"error": "Judy had nothing to say. Try again."}, 502
    return {"reply": reply, "tier": summary["tier"]}