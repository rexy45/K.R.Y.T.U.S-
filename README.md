<<<<<<< HEAD
# Krytus - Autonomous Personal AI Chief of Staff

A production-ready personal AI assistant accessible via Telegram with tool-calling, long-term memory, outbound calls/SMS, email, and scheduled reminders.

## Quick Start

```bash
# 1. Initialize project with uv
uv init krytus
cd krytus

# 2. Install dependencies
uv add openai python-telegram-bot twilio chromadb apscheduler python-dotenv

# 3. Copy environment template
cp .env.example .env

# 4. Edit .env with your credentials (see Configuration below)

# 5. Run
uv run python -m src.main
```

## Configuration

Copy `.env.example` to `.env` and fill in all values:

### Required Credentials

| Variable | Source |
|----------|--------|
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram |
| `MY_TELEGRAM_CHAT_ID` | Message [@userinfobot](https://t.me/userinfobot) on Telegram |
| `TWILIO_ACCOUNT_SID` | [Twilio Console](https://console.twilio.com) |
| `TWILIO_AUTH_TOKEN` | [Twilio Console](https://console.twilio.com) |
| `TWILIO_PHONE_NUMBER` | Verified Twilio number (E.164: `+15551234567`) |
| `MY_PHONE_NUMBER` | Your personal number (E.164 format) |
| `SMTP_USERNAME` | Your Gmail address |
| `SMTP_PASSWORD` | [Gmail App Password](https://myaccount.google.com/apppasswords) (requires 2FA) |
| `EMAIL_FROM` | Same as SMTP_USERNAME |

### Gmail App Password Setup
1. Enable 2-Factor Authentication on your Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Create an app password for "Mail"
4. Use that 16-character password as `SMTP_PASSWORD`

### Twilio Setup
1. Create a Twilio account at https://twilio.com
2. Buy a phone number (Voice + SMS capable)
3. Verify your personal phone number in Twilio Console (for trial accounts)
4. Copy Account SID and Auth Token

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/status` | Health check |
| `/memory` | View recent long-term memories |
| `/reminders` | List pending reminders |

## Natural Language Usage

Just chat with Krytus naturally. Examples:

- *"Schedule a reminder for 30 minutes: Review the PRD"*
- *"Email sarah@company.com with subject 'Q3 Update' and tell her the launch is on track"*
- *"Call me and say 'Server deployment completed successfully'"*
- *"Text me the AWS account ID"*
- *"Save this decision: We're using PostgreSQL for the new analytics DB because of JSONB support"*
- *"What did we decide about the caching layer last week?"* (triggers proactive recall)

## Architecture

```
src/
├── main.py       # Telegram bot + APScheduler
├── agent.py      # OpenAI tool-calling loop
├── tools.py      # All tool implementations (email, Twilio, ChromaDB, SQLite)
└── config.py     # Environment configuration
```

### Data Storage
- **ChromaDB** (`./data/chromadb/`): Vector embeddings for semantic memory
- **SQLite** (`./data/krytus.db`): Reminder queue with delivery tracking

### Background Scheduler
- Checks reminders every 30 seconds
- Delivers via Telegram to `MY_TELEGRAM_CHAT_ID`
- Marks delivered reminders to prevent duplicates

## Security

- Single-user only: messages from any other `chat_id` are silently dropped
- All credentials via environment variables
- No secrets in code

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## License

MIT
=======
# K.R.Y.T.U.S-
An intelligent multi-model AI CLI built by Dream_Forge AI 
>>>>>>> dd14f56123c1c13343abab31aa830e99b9818e1b
