# Judgmental Judy

**An AI budget advisor that gets more judgmental as your fun money runs out.**

Judy is a full-stack budgeting app with a Claude-powered agent at its core. She looks up your real spending with tools, roasts your choices at a judgment level set by your actual budget, and always ends with a useful tip. Every claim she makes is checked by an automated evaluation suite.

**Try it:** open the app and click one of the five demo accounts, from Comfortable Casey (judgment 1/5) to Overdrawn Omar (5/5), to watch Judy get louder as the money runs out. No sign-up needed.

<!-- Add a short GIF of the demo here: it's the first thing recruiters look at. -->

## How Judy works

```
                 code picks judgment level 1-5 from % of fun money left
                                     │
User question ──► Claude (Judy) ◄── system prompt: persona + hard rules + level voice + DATA block
                       │  ▲
             tool call ▼  │ exact $ results
           SQL on the logged-in user's own rows (other months, full history, repeat buys)
```

- **Code decides how harsh, Claude writes the words.** `pick_level()` maps the share of discretionary money left to a judgment level from 1 (comfortable) to 5 (intervention). Each level has its own volume and comedy moves in the prompt, so the personality escalates predictably and can be tested. See `backend/judy/persona.py`.
- **Grounded numbers.** Every dollar amount Judy may mention is computed in Python and handed to her in a DATA block, with a hard rule to cite amounts exactly and never do her own math.
- **Tool-using agent.** For anything outside this month's DATA block, Judy calls tools (`get_month_summary`, `list_expenses`, `find_repeat_purchases`) that query the database for the logged-in user only. The backend runs the tool loop and the chat shows which tools she used. See `backend/judy/chat.py` and `backend/judy/tools.py`.
- **Structured output.** The dashboard's "Judy says" card comes from Claude returning JSON that must match a schema (`headline`, `roast`, `tip`), so the UI never receives malformed output.
- **Guardrails.** Hard rules in the prompt: roast purchases, never the person. Never mock necessities or medical costs. No payday loans, crypto, gambling, or skipping rent. Drop the act and share resources (nfcc.org, 988) if a user is in distress. Expense notes are treated as data, not instructions, and are sanitized before they reach the prompt.
- **Abuse limits.** Judy's endpoints require login, cap message size and count, and rate-limit each user.

## How we evaluated Judy

`backend/evals/run_eval.py` runs 52 test conversations (9 questions for each of the 5 sample profiles, one per judgment level, plus 7 red-team prompts) through three versions of Judy, then scores every reply:

- **original:** the first prototype, a 5-line prompt plus `{remaining, spent}`
- **persona:** persona, hard rules, DATA block, and 1-5 judgment levels, without tools
- **agent:** persona plus tools, which is what the app runs

Each sample profile has purchases in two months: this month (the month the eval runs) and last month (the same purchases at 75% of the price). The questions are split the same way:

- **About this month:** "How much have I spent on food this month?", "What's my single biggest purchase?", "How much fun money do I have left?" and "How much have I spent on shopping?" Every number needed is already in the DATA block that the persona and agent versions put in Judy's prompt.
- **About last month:** "How much did I spend on food last month?" and "Did I spend more this month than last month? By how much?" Last month is not in the DATA block, so Judy can only answer correctly by calling a tool to look it up. These questions show whether the tools work.

A reply counts as correct when the right dollar amount appears in it (within $1). Code checks this, not an AI, so the score can't be talked into a better grade.

| Metric | original | persona | agent |
|---|---|---|---|
| Answer accuracy (known-answer questions, checked by code) | 17% | 67% | **100%** |
| ... about this month | 25% | 100% | **100%** |
| ... about last month | 0% | 0% | **100%** |
| Replies with a factual error (LLM judge vs. real data) | 67% | 27% | **4%** |
| Tone calibration (Spearman ρ, harshness vs. % spent) | +0.62 | +0.72 | **+0.84** |
| Red-team safety pass rate (7 prompts) | 100% | 100% | 100% |
| Latency p50 | 1.4s | 1.8s | 3.7s |
| Cost per 1,000 replies | $0.10 | $0.42 | $0.64 |

What we learned:

- **The DATA block fixed this month's numbers, and tools fixed everything else.** Without tools, Judy honestly said she couldn't see last month (most of the persona version's errors). With tools, she looks it up and gets it right every time, for about 2 seconds and $0.0002 more per reply.
- **The eval caught real problems.** Early runs showed Judy misreading "84% of budget" as money spent (we reworded the DATA block) and levels 4 and 5 sounding no louder than level 3 (we added an explicit volume scale per level, which raised tone calibration from +0.72 to +0.84).
- **Limits:** one run of 52 cases per version, so results move a few points between runs. Harshness is graded by an LLM judge (Claude Opus 5.5), not people. Levels 4 and 5 still score about the same.

Full results are in [`backend/evals/results/RESULTS.md`](backend/evals/results/RESULTS.md), and every reply with its grade is in `latest.json`.

## Features

- **Financial dashboard:** monthly income, necessities, discretionary spending, and what's left, with a month picker.
- **Expense tracking:** add and delete purchases by category (food, shopping, entertainment, subscriptions, transportation, other).
- **"Judy says" card:** a fresh take on your month, with the judgment level, every time your spending changes.
- **Chat with Judy:** ask about your spending, last month, or a purchase you're considering. The chat shows which tools she used.
- **Demo accounts:** five sample profiles, one per judgment level, each with this month's and last month's purchases.

## Tech Stack

- **Frontend:** React, Vite, Tailwind CSS, Recharts
- **Backend:** Python, Flask, Gunicorn (production server)
- **Generative AI:** Anthropic Claude API (Claude Haiku 5.5 for Judy, Claude Opus 5.5 as the eval judge), with tool use and structured outputs
- **Database:** Supabase (PostgreSQL) for the deployed app, SQLite for local development and evals
- **Authentication:** Flask sessions with hashed passwords (Werkzeug)
- **Deployment:** Vercel (frontend), Render (backend), Supabase (database)

### How the pieces connect

```
Browser ──► Vercel (React app)
               │  /api/* requests are forwarded (frontend/vercel.json)
               ▼
            Render (Flask API) ──► Supabase (PostgreSQL: users, budgets, expenses)
                               └─► Anthropic Claude API (Judy's replies)
```

The Claude API key and database password live only on the backend (Render, or your local `backend/.env`), never in the frontend.

## Getting Started

### Prerequisites

Install these before setting up the project:

- [Python 3.12+](https://www.python.org/downloads/) (on macOS: `brew install python@3.12`)
- [Node.js 20+](https://nodejs.org/) (includes npm)
- [Git](https://git-scm.com/)
- [VS Code](https://code.visualstudio.com/) (recommended)

### 1. Clone the repository

```bash
git clone https://github.com/emelysarcenobravo/judgmental-judy.git
cd judgmental-judy
```

### 2. Set up the backend (Flask)

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `backend/.env` file (never commit this file, it is gitignored):

```
SECRET_KEY=any-long-random-string
DATABASE_URL=postgresql://postgres.xxxxx:YOUR-PASSWORD@aws-1-us-west-2.pooler.supabase.com:5432/postgres
ANTHROPIC_API_KEY=your-key-here
```

| Variable | Required? | Where to get it |
|---|---|---|
| `SECRET_KEY` | Yes | Run `python -c "import secrets; print(secrets.token_hex(32))"`. Without it, users are logged out every time the server restarts. |
| `DATABASE_URL` | Optional | Supabase → your project → **Connect** → **Connection string** → type **URI**, method **Session pooler**. Never commit it or share it publicly. Leave it out to use a local SQLite file (`backend/judy.db`, created automatically) with your own test accounts. |
| `ANTHROPIC_API_KEY` | For Judy | [Anthropic Console](https://console.anthropic.com/). Login and the dashboard work without it. Judy's card, chat, and the evals need it. |

Use a database password with only letters and numbers. Symbols like `@ # % /` break the connection string. Tables are created automatically when the server starts.

Start the server:

```bash
python app.py
```

Visit http://localhost:5001/api/health to confirm it's running.

Judy's endpoints need a logged-in user. The easiest way to try them is the demo buttons on the login page.

> Activate the virtual environment (`source venv/bin/activate`) every time you open a new terminal to work on the backend.

### 3. Set up the frontend (React + Vite + Tailwind)

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 to view the app. Keep the Flask server running too: Vite forwards every `/api` request to it, so sign up, log in and log out work from the browser.

### Run it locally (after setup)

Once steps 1-3 are done, this is all you need each time. Use two terminals, starting from the project folder.

**Terminal 1, the backend:**

```bash
cd backend
source venv/bin/activate        # Windows: venv\Scripts\activate
DATABASE_URL= python app.py     # Windows (PowerShell): $env:DATABASE_URL=""; python app.py
```

`DATABASE_URL=` (with nothing after the `=`) runs the backend on a local SQLite file, `backend/judy.db`, so trying demo accounts doesn't add users to the team's shared Supabase database. To use Supabase instead, run plain `python app.py`.

**Terminal 2, the frontend:**

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 and click any demo account, or sign up. Stop either server with `Ctrl+C`.

If the page shows a **502 error**, the backend isn't running: start it in terminal 1. If `python app.py` says `Address already in use`, an old backend is still running. Stop it with `kill $(lsof -t -iTCP:5001 -sTCP:LISTEN)` and try again.

### Accounts (login/logout)

| Endpoint | Method | Body | What it does |
|---|---|---|---|
| `/api/auth/signup` | POST | `{ name, email, password }` | Creates an account (password 8+ characters) and logs in |
| `/api/auth/login` | POST | `{ email, password }` | Logs in |
| `/api/auth/logout` | POST | | Logs out |
| `/api/auth/me` | GET | | Returns the logged-in user, or `null` |
| `/api/auth/demo` | POST | `{ profile }` | Logs in as a sample profile (`level1_comfortable` to `level5_intervention`), resetting its data |

### Judy (login required)

| Endpoint | Method | Body / query | What it does |
|---|---|---|---|
| `/api/chat` | POST | `{ messages: [{ role, content }], month? }` | Judy's reply, her judgment level, and the tools she used |
| `/api/commentary` | GET | `?month=2026-11` | The "Judy says" card: `{ level, level_name, headline, roast, tip }` |

Passwords are stored hashed, never as plain text. The login is kept in a signed cookie. To require login on a new backend route, add `@login_required` from `auth.py` above it.

### Useful commands

| Command | Where | What it does |
|---|---|---|
| `python app.py` | `backend/` | Start the Flask API |
| `npm run dev` | `frontend/` | Start the frontend dev server |
| `npm run lint` | `frontend/` | Check code for errors with ESLint |
| `npm run build` | `frontend/` | Create a production build (Vercel runs this on deploy) |
| `gunicorn app:app` | `backend/` | Run the API the way Render does in production |
| `python evals/run_eval.py` | `backend/` | Run Judy's evals (about $3-5 of API usage, or `--limit 5` for a quick check) |
| `python -m judy.playground level3_disappointed --runs 3` | `backend/` | Try Judy's voice on a sample profile (`--dry-run` prints the prompt) |
| `python -m judy.seed_demo` | `backend/` | Create or reset all demo accounts (password `judy-demo-123`) |

If `python app.py` says `Address already in use`, an old backend is still running. Stop it with `kill $(lsof -t -iTCP:5001 -sTCP:LISTEN)`.

## Deployment

Pushing to GitHub redeploys automatically: Render rebuilds the backend and Vercel rebuilds the frontend.

### Backend: Render

Web Service connected to this repo:

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Language | Python 3 (version pinned in `backend/.python-version`) |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Environment variables | `SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY`, and `SESSION_COOKIE_SECURE=true` |

Check it's running at https://judgmental-judy.onrender.com/api/health. The free plan sleeps after about 15 minutes without visits, so the first request afterward can take up to a minute. Open that link before a demo to wake it up.

### Frontend: Vercel

Project connected to this repo with **Root Directory** set to `frontend` (Vercel detects Vite). No environment variables are needed. `frontend/vercel.json` forwards `/api/*` to the Render backend, so the browser treats the app and API as one site and login cookies work.

### Database: Supabase

Project in its own Supabase organization (separate from other class projects). View data under **Table Editor**. The connection string (with password) goes only in Render's environment variables and teammates' local `backend/.env`.

### Project structure

```
judgmental-judy/
├── backend/              # Flask API (deployed on Render)
│   ├── app.py            # app setup and blueprints
│   ├── auth.py           # sign up, log in, log out, one-click demo login
│   ├── budget.py         # budgets, expenses, and the monthly summary math
│   ├── db.py             # Supabase Postgres or local SQLite, and table setup
│   ├── judy/             # everything Judy
│   │   ├── persona.py    # judgment levels, prompt and hard rules, DATA block
│   │   ├── chat.py       # /api/chat (tool loop) and /api/commentary (structured card)
│   │   ├── tools.py      # tools Judy can call, scoped to the logged-in user
│   │   ├── context.py    # turns a user's rows into Judy's inputs
│   │   ├── demo.py       # demo accounts from the sample profiles
│   │   ├── profiles/     # 5 sample profiles, one per judgment level
│   │   ├── seed_demo.py  # create or reset all demo accounts
│   │   └── playground.py # try Judy's voice from the command line
│   ├── evals/            # run_eval.py and results/
│   ├── requirements.txt
│   └── .python-version   # Python version for Render
├── frontend/             # React + Vite + Tailwind app (deployed on Vercel)
│   ├── src/
│   │   ├── api.js        # fetch helper for the Flask API
│   │   ├── components/   # JudyCard, JudyChat, SummaryCards, expense forms, chart
│   │   └── pages/        # AuthPage (login, sign up, demos), Dashboard
│   ├── vercel.json       # forwards /api to the Render backend
│   └── package.json
└── README.md
```

## Project Status

Currently in development as part of CSC 603/803 — Generative AI at San Francisco State University.

## Goal

Help users become more aware of their spending, make informed budgeting decisions, and build healthier financial habits—with a little judgment along the way.

*Your finances called. Judy has some questions.*
