"""Throwaway playground for tuning Judy's personality.

Run from the backend/ folder (with your venv active):

    python -m judy.playground tier3_disappointed              # one run
    python -m judy.playground tier3_disappointed --runs 5    # same profile 5 times
    python -m judy.playground all --runs 3             # every profile, 3 runs each
    python -m judy.playground tier4_intervention --runs 5 --message "Can I afford new AirPods?"
    python -m judy.playground tier4_intervention --dry-run    # print the prompt, no API call
"""

import argparse
import os
from pathlib import Path

from judy.persona import (
    build_system_prompt,
    compute_summary,
    list_profiles,
    load_profile,
    money,
    unverified_amounts,
)

DEFAULT_MODEL = "claude-haiku-5-5"  # same model app.py uses
COMMENTARY_REQUEST = "Look at my month so far and give me your take."


def ask_judy(client, model, system, user_message):
    """One Claude call. Mirrors the settings in app.py's /api/chat."""
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": user_message}],
        output_config={"effort": "low"},
    )
    if response.stop_reason == "refusal":
        return "[model refused]"
    return next((b.text for b in response.content if b.type == "text"), "").strip()


def run_profile(client, args, name):
    profile = load_profile(name)
    summary = compute_summary(profile)
    system = build_system_prompt(profile, summary)

    left = money(summary["left"])
    print("=" * 72)
    print(f"{profile['name']}  |  tier: {summary['tier']}  |  "
          f"{summary['percent_left']}% left ({left} of {money(summary['discretionary'])})")
    print("=" * 72)

    if args.dry_run:
        print(system)
        print()
        return

    user_message = args.message or COMMENTARY_REQUEST
    print(f"User: {user_message}\n")
    for i in range(1, args.runs + 1):
        reply = ask_judy(client, args.model, system, user_message)
        print(f"[run {i}] {reply}")
        bad = unverified_amounts(reply, system)
        if bad:
            print(f"         ⚠ check these amounts, not in the data: {', '.join(f'${b:,.2f}' for b in bad)}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Try Judy against a sample profile.")
    parser.add_argument("profile", help=f"profile name or 'all'. Available: {', '.join(list_profiles())}")
    parser.add_argument("--runs", type=int, default=1, help="how many times to ask Judy")
    parser.add_argument("--message", help="chat message to send instead of the default commentary request")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="print the prompt without calling the API")
    args = parser.parse_args()

    client = None
    if not args.dry_run:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise SystemExit("Add ANTHROPIC_API_KEY to backend/.env first.")
        import anthropic

        client = anthropic.Anthropic()

    names = list_profiles() if args.profile == "all" else [args.profile]
    for name in names:
        run_profile(client, args, name)


if __name__ == "__main__":
    main()
