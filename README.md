# Judgmental Judy

**Your judgmental AI budget advisor.**

Judgmental Judy is a generative AI-powered budgeting application that helps users track expenses, manage discretionary spending, and identify opportunities to cut back on excessive spending habits. Powered by Anthropic's Claude, Judy analyzes users' financial information and delivers personalized insights with a witty, sarcastic, and increasingly judgmental personality as their discretionary budget decreases.

## Features

- **Financial Dashboard:** View monthly income, necessary expenses, discretionary spending, and remaining available cash.
- **Expense Tracking:** Manually enter transactions and organize spending into categories such as food, shopping, entertainment, and subscriptions.
- **Discretionary Budgeting:** Calculate available discretionary income after accounting for monthly necessities and track how much remains.
- **Spending Analysis:** Identify potentially excessive spending, recurring purchases, and questionable financial habits.
- **AI Budget Advisor:** Receive personalized financial observations and recommendations from Judy, with increasingly judgmental commentary as discretionary funds decrease.
- **Interactive Chat:** Ask Judy questions about your finances, spending habits, and purchasing decisions through a conversational chatbot.
- **Sample Financial Profiles:** Explore the application using predefined financial scenarios without entering personal financial information.

## How Judy Works

The application uses traditional programming logic to process financial information, calculate budgets, and track spending. This structured financial data is then passed to Claude, which interprets spending patterns and generates personalized feedback.

Judy interacts with users in two ways:

- **Dashboard Commentary:** Judy automatically provides sarcastic observations about spending habits and reacts to changes in discretionary spending.
- **Conversational Chatbot:** Users can interact directly with Judy to ask questions, discuss financial decisions, and receive personalized advice.

Judy's judgmental personality escalates as users approach their discretionary spending limits, while maintaining a humorous and helpful approach to financial awareness.

## Tech Stack

- **Frontend:** React, Vite, Tailwind CSS, Recharts
- **Backend:** Python, Flask
- **Database:** SQLite
- **Generative AI:** Anthropic Claude API
- **Development:** VS Code, Git, GitHub, ESLint
- **Deployment:** Vercel (frontend), backend hosting TBD

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

Create a `backend/.env` file for your Claude API key and a secret key for login sessions (never commit this file):

```
ANTHROPIC_API_KEY=your-key-here
SECRET_KEY=any-long-random-string
```

Generate a `SECRET_KEY` with `python -c "import secrets; print(secrets.token_hex(32))"`. Without it, users are logged out every time the server restarts.

**Database:** without a `DATABASE_URL`, the app uses a local SQLite file (`backend/judy.db`, created automatically and gitignored), so each teammate has their own local accounts. To use the shared Supabase Postgres database instead, add its connection string to `backend/.env`:

```
DATABASE_URL=postgresql://postgres.xxxxx:YOUR-PASSWORD@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

Find it in Supabase under **Connect** → **Connection string** → **Session pooler**. The `users` table is created automatically on startup.

Start the server:

```bash
python app.py
```

Visit http://localhost:5001/api/health to confirm it's running.

Test Judy's chat endpoint (requires your API key in `backend/.env`):

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "I spent $80 on boba this week"}]}'
```

> Activate the virtual environment (`source venv/bin/activate`) every time you open a new terminal to work on the backend.

### 3. Set up the frontend (React + Vite + Tailwind)

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 to view the app. Keep the Flask server running too: Vite forwards every `/api` request to it, so sign up, log in and log out work from the browser.

### Accounts (login/logout)

| Endpoint | Method | Body | What it does |
|---|---|---|---|
| `/api/auth/signup` | POST | `{ name, email, password }` | Creates an account (password 8+ characters) and logs in |
| `/api/auth/login` | POST | `{ email, password }` | Logs in |
| `/api/auth/logout` | POST | | Logs out |
| `/api/auth/me` | GET | | Returns the logged-in user, or `null` |

Passwords are stored hashed, never as plain text. The login is kept in a signed cookie. To require login on a new backend route, add `@login_required` from `auth.py` above it.

### Useful commands

| Command | Where | What it does |
|---|---|---|
| `python app.py` | `backend/` | Start the Flask API |
| `npm run dev` | `frontend/` | Start the frontend dev server |
| `npm run lint` | `frontend/` | Check code for errors with ESLint |
| `npm run build` | `frontend/` | Create a production build (Vercel runs this on deploy) |

### Project structure

```
judgmental-judy/
├── backend/          # Flask API
│   ├── app.py        # app setup and Judy's chat endpoint
│   ├── auth.py       # sign up, log in, log out
│   ├── db.py         # SQLite connection and tables
│   └── requirements.txt
├── frontend/         # React + Vite + Tailwind app
│   ├── src/
│   │   ├── api.js    # fetch helper for the Flask API
│   │   └── pages/    # AuthPage (login/sign up), Dashboard
│   └── package.json
└── README.md
```

## Project Status

Currently in development as part of CSC 603/803 — Generative AI at San Francisco State University.

## Goal

Help users become more aware of their spending, make informed budgeting decisions, and build healthier financial habits—with a little judgment along the way.

*Your finances called. Judy has some questions.*
