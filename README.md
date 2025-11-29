# 🎓 Bottel - Vocabulary Learning Bot

A Telegram bot that helps you learn advanced English vocabulary (C1-C2 level) from Twitter using **spaced repetition** (memory curve).

## ✨ Features

- 📚 **Twitter Integration**: Fetches vocabulary from your Twitter feed
- 🧠 **Spaced Repetition**: Reviews words based on the Ebbinghaus forgetting curve
  - 24 hours → 2-3 days → 1 week → 2 weeks → 1 month
- ✅ **Read Tracking**: Confirm when you've read words
- ⏰ **Persistent Reminders**: Get notified every 5 minutes until you confirm reading
- 🤖 **AI-Powered**: Uses Gemini to extract C1-C2 vocabulary and generate definitions

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt

# Install Playwright browsers (optional, for authenticated Twitter)
playwright install chromium
```

### 2. Configure Environment

Edit `.env` with your credentials:

```env
# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=your_token_here

# Gemini API Key (free at https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_key

# Twitter Credentials (optional, for authenticated feed)
TWITTER_USERNAME=your_email
TWITTER_PASSWORD=your_password
```

### 3. Run the Bot

```bash
python main.py
```

### 4. Start Learning

1. Open Telegram and find your bot (`@advanceden_bot`)
2. Send `/start` to register
3. Send `/fetch` to get vocabulary from Twitter
4. Send `/words` to receive your daily vocabulary

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and see welcome message |
| `/fetch` | Fetch new vocabulary from Twitter |
| `/words` | Get today's vocabulary batch |
| `/review` | Get words due for review |
| `/stats` | View your learning statistics |
| `/add <word>` | Manually add a word to learn |
| `/help` | Show help message |

## 🔄 How Spaced Repetition Works

The bot uses the **Ebbinghaus forgetting curve** to optimize memory retention:

```
New Word → 24h Review → 2-3 Days → 1 Week → 2 Weeks → 1 Month → Mastered! 🏆
```

Each time you confirm reading, the word advances to the next stage. If you don't confirm, you'll get reminders every 5 minutes.

## 📅 Automatic Schedule

The bot runs on autopilot:

- **6:30 AM**: Fetches new vocabulary from Twitter
- **7:00 AM**: Sends daily vocabulary batch
- **Every hour**: Checks for words due for review
- **Every 5 min**: Sends reminders for unread batches

## 🏗️ Project Structure

```
bottel/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env                 # Configuration (create from .env.example)
└── src/
    ├── bot.py           # Telegram bot handlers
    ├── database.py      # SQLite database models
    ├── scheduler.py     # Automated tasks
    └── twitter_scraper.py # Twitter + Gemini integration
```

## 🔧 Configuration

### Twitter Accounts for Vocabulary

By default, the bot fetches from these accounts known for rich vocabulary:
- The Economist, The Guardian, NYTimes, The Atlantic, New Yorker, NPR, BBC, FT

You can modify the list in `src/twitter_scraper.py`.

## 🚀 Deploy to Railway (Free)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Go to **Variables** tab and add these environment variables:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | `8413539238:AAH8JVrEEFqucl8Opu5bHonjd0sEaERoMNQ` |
| `GEMINI_API_KEY` | `AIzaSyAFUprxVYsLxnxVxUoK9hgyoKqDlRKO5QM` |
| `TWITTER_USERNAME` | `fati01saleh@gmail.com` |
| `TWITTER_PASSWORD` | `Fatimaalisaleh-2001` |

5. Click **Deploy** - done! 🎉

Your bot will now run 24/7 for free.

## 📝 License

MIT License

