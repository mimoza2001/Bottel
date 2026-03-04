# Bottel

A Telegram bot that wraps [Discounted Udemy Course Enroller (DUCE)](https://github.com/techtanic/Discounted-Udemy-Course-Enroller) — automatically scrape free/discounted Udemy courses from multiple coupon sites and enroll in them, all from Telegram.

## Features

- **Telegram-native interface** — interact entirely via bot commands
- **Per-user sessions** — each user has their own Udemy credentials and settings
- **Inline keyboard configuration** — toggle sites, languages, and categories with buttons
- **Real-time progress** — enrollment progress is streamed back as Telegram messages
- **Persistent settings** — per-user settings are saved to disk between bot restarts

## Supported Scraping Sites

Real Discount · Courson · IDownloadCoupons · E-next · Discudemy · Udemy Freebies · Course Joiner · Course Vania

## Setup

### 1. Clone and install dependencies

```bash
git clone <this-repo>
cd Bottel
pip install -r requirements.txt
```

### 2. Create a Telegram bot

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the API token you receive

### 3. Set the bot token

```bash
export TELEGRAM_BOT_TOKEN="your-token-here"
```

### 4. Run the bot

```bash
python bot.py
```

## Bot Commands

| Command | Description |
|---|---|
| `/start` or `/help` | Show welcome message and command list |
| `/login <email> <password>` | Authenticate with Udemy |
| `/run` | Scrape sites and enroll in available courses |
| `/status` | Show session info and last-run stats |
| `/settings` | Display current settings |
| `/setsites` | Toggle which scraping sites to use |
| `/setlanguages` | Toggle which course languages to accept |
| `/setcategories` | Toggle which course categories to accept |
| `/setminrating <0-5>` | Set minimum course rating |
| `/excludeinstructor <slug>` | Block courses from a specific instructor |
| `/excludekeyword <word>` | Block courses whose title contains a keyword |
| `/clearexclusions` | Remove all instructor/keyword exclusions |
| `/discountedonly` | Toggle discounted-only mode (skip free courses) |

## Architecture

```
bot.py          — Telegram bot (python-telegram-bot v20+, async)
base.py         — Core scraping & enrollment engine (from DUCE)
default-duce-bot-settings.json  — Default settings template
user_data/      — Per-user settings files (auto-created at runtime)
```

`BotUdemy` (defined in `bot.py`) extends `Udemy` from `base.py` to provide
per-user, file-backed settings stored at `user_data/<chat_id>-settings.json`.

## Credits

Core enrollment engine: [techtanic/Discounted-Udemy-Course-Enroller](https://github.com/techtanic/Discounted-Udemy-Course-Enroller)
