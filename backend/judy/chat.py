"""POST /api/chat (talk to Judy) and GET /api/commentary (her dashboard card).

The browser sends ONLY the conversation. Every number Judy sees is read from the
database for the logged-in user, so nobody can feed her fake figures. This month's
numbers go in the system prompt's DATA block, and tools let her look up anything else.
"""

import json
import os
import time
import hashlib                                  # add
import json
import os
import time
from collections import OrderedDict, defaultdict, deque   # add OrderedDict
from collections import defaultdict, deque
from functools import wraps

import anthropic
from flask import Blueprint, request, session

from auth import login_required
from db import get_db
from judy.context import build_judy_inputs
from judy.persona import LEVELS, build_system_prompt
from judy.tools import TOOLS, run_tool

judy = Blueprint("judy", __name__, url_prefix="/api")

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 16000         # a ceiling, not a target: replies are ~100 words, but tool turns and thinking need room
MAX_TOOL_ROUNDS = 4        # stops a confused model from looking things up forever
MAX_MESSAGES = 20          # most recent turns the browser may send
MAX_MESSAGE_CHARS = 1000

# Simple in-memory rate limit per user. Fine for one gunicorn worker (Render's default),
# but with several workers each would count separately.
RATE_LIMITS = {"chat": 60, "commentary": 120}  # requests...
RATE_WINDOW_SECONDS = 600                       # ...per 10 minutes
_recent_requests = defaultdict(deque)

# Cache for the dashboard card. The key is the user plus a hash of the whole system prompt,
# which holds the level, today's date and every number, so any change to spending (or a new
# day) is automatically a different key. In memory, so each gunicorn worker has its own.
CARD_CACHE_MAX = 200
CARD_CACHE_SECONDS = 3600
_card_cache = OrderedDict()  # (user_id, prompt hash) -> (saved_at, card)

REFUSAL_CARD = {"headline": "No comment.", "roast": "Judy is choosing silence today.", "tip": "Log a few expenses and check back."}

COMMENTARY_REQUEST = """Write your dashboard card about this month. Same voice and rules as always,
but split it into three parts: a punchy headline of at most 6 words, a roast of 1-2 sentences,
and one tip (without a "Tip:" label)."""

COMMENTARY_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "roast": {"type": "string"},
        "tip": {"type": "string"},
    },
    "required": ["headline", "roast", "tip"],
    "additionalProperties": False,
}

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _client


def rate_limited(user_id, kind):
    now = time.monotonic()
    recent = _recent_requests[(user_id, kind)]
    while recent and now - recent[0] > RATE_WINDOW_SECONDS:
        recent.popleft()
    if len(recent) >= RATE_LIMITS[kind]:
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


def ask_judy(db, user_id, messages, system, use_tools=True):
    """Run the conversation through Claude, letting it call tools until it has an answer.
    Returns {reply, tools_used, usage}. Anthropic API errors are left for the caller."""
    messages = list(messages)
    tools_used = []
    usage = {"input_tokens": 0, "output_tokens": 0}

    for round_number in range(MAX_TOOL_ROUNDS + 1):
        last_round = round_number == MAX_TOOL_ROUNDS
        response = get_client().messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
            output_config={"effort": "low"},
            **({"tools": TOOLS} if use_tools else {}),
            # Last call: keep the tools defined (the history contains tool calls) but
            # forbid using them, so Claude has to write its answer.
            **({"tool_choice": {"type": "none"}} if use_tools and last_round else {}),
        )

        usage["input_tokens"] += response.usage.input_tokens
        usage["output_tokens"] += response.usage.output_tokens

        if response.stop_reason == "refusal":
            reply = "Even Judy won't touch that one. Ask me about your budget instead."
            return {"reply": reply, "tools_used": tools_used, "usage": usage}
        if response.stop_reason != "tool_use":
            break

        # Claude asked for data: run every tool it called and send all the results back together.
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tools_used.append(block.name)
            try:
                content, is_error = run_tool(db, user_id, block.name, block.input), False
            except ValueError as e:
                content, is_error = str(e), True
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error})
        messages.append({"role": "user", "content": results})

    reply = "".join(b.text for b in response.content if b.type == "text").strip()
    return {"reply": reply, "tools_used": tools_used, "usage": usage}

def cached_card(user_id, system):
    """(key, card). card is None on a miss."""
    key = (user_id, hashlib.sha256(system.encode()).hexdigest())
    hit = _card_cache.get(key)
    if hit and time.monotonic() - hit[0] < CARD_CACHE_SECONDS:
        return key, hit[1]
    return key, None


def remember_card(key, card):
    _card_cache[key] = (time.monotonic(), card)
    _card_cache.move_to_end(key)
    while len(_card_cache) > CARD_CACHE_MAX:
        _card_cache.popitem(last=False)  # drop the oldest

def write_card(system):
    """Judy's dashboard card as {headline, roast, tip}. The schema guarantees valid JSON."""
    response = get_client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": COMMENTARY_REQUEST}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": COMMENTARY_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        return REFUSAL_CARD
    card = json.loads(next(b.text for b in response.content if b.type == "text"))
    card["tip"] = card["tip"].removeprefix("Tip:").strip()  # the UI adds its own "Tip:" label
    return card


def claude_endpoint(kind, limit = True):
    """Shared checks for Judy's endpoints: API key, rate limit, and friendly Claude errors."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not os.getenv("ANTHROPIC_API_KEY"):
                return {"error": "Judy isn't connected to Claude yet (missing ANTHROPIC_API_KEY)"}, 500
            if limit and rate_limited(session["user_id"], kind):
                return {"error": "Judy needs a breather. Try again in a few minutes."}, 429
            try:
                return view(*args, **kwargs)
            except anthropic.AuthenticationError:
                return {"error": "Invalid ANTHROPIC_API_KEY"}, 500
            except anthropic.RateLimitError:
                return {"error": "Judy needs a breather. Try again in a moment."}, 429
            except anthropic.APIStatusError as e:
                return {"error": e.message}, 502
            except anthropic.APIConnectionError:
                return {"error": "Could not reach the Claude API"}, 502
        return wrapped
    return decorator


def load_inputs(month):
    """(profile, summary, error response) for the logged-in user."""
    try:
        profile, summary = build_judy_inputs(get_db(), session["user_id"], month)
    except ValueError as e:  # bad month format
        return None, None, ({"error": str(e)}, 400)
    if profile is None:
        return None, None, ({"error": "Set up your budget first so Judy has something to judge"}, 400)
    return profile, summary, None


def level_fields(summary):
    if summary["discretionary"] <= 0:  # bills alone exceed income: no judgment level applies
        return {"level": 0, "level_name": "tight month"}
    return {"level": summary["level"], "level_name": LEVELS[summary["level"]]["name"]}

@judy.post("/chat")
@login_required
@claude_endpoint("chat")
def chat():
    data = request.get_json(silent=True) or {}
    messages, error = clean_messages(data.get("messages"))
    if error:
        return {"error": error}, 400
    profile, summary, error = load_inputs(data.get("month"))
    if error:
        return error

    result = ask_judy(get_db(), session["user_id"], messages, build_system_prompt(profile, summary))
    if not result["reply"]:
        return {"error": "Judy had nothing to say. Try again."}, 502
    return {"reply": result["reply"], "tools_used": result["tools_used"], **level_fields(summary)}


@judy.get("/commentary")
@login_required
@claude_endpoint("commentary", limit=False)  # limit is checked below, only when Claude is called
def commentary():
    profile, summary, error = load_inputs(request.args.get("month"))
    if error:
        return error
    system = build_system_prompt(profile, summary)
    key, card = cached_card(session["user_id"], system)
    if card is None:
        if rate_limited(session["user_id"], "commentary"):
            return {"error": "Judy needs a breather. Try again in a few minutes."}, 429
        card = write_card(system)
        if card is not REFUSAL_CARD:
            remember_card(key, card)
    return {**card, **level_fields(summary)}