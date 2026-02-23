# Browser Automation & Social Media Skills

AI-powered browser automation for social media posting, web scraping, and automated interactions using Playwright.

## Available Commands

- `/post-social` — Draft and post content to Twitter/X, LinkedIn, Threads, or Bluesky
- `/browser-automate` — Automate any browser-based workflow with Playwright
- `/scrape-web` — Extract structured data from any webpage
- `/social-schedule` — Schedule and queue social media posts

## Setup

Install Playwright and dependencies:
```bash
npm install playwright @playwright/test
npx playwright install chromium firefox webkit

pip install playwright tweepy python-linkedin-v2 requests python-dotenv
```

Required environment variables in `.env`:
```
# Twitter/X
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# LinkedIn
LINKEDIN_CLIENT_ID=your_id
LINKEDIN_CLIENT_SECRET=your_secret
LINKEDIN_ACCESS_TOKEN=your_token

# Threads / Instagram
THREADS_USERNAME=your_username
THREADS_PASSWORD=your_password

# Bluesky
BLUESKY_HANDLE=your.handle.bsky.social
BLUESKY_APP_PASSWORD=your_app_password
```

## Security Notes

- Never commit `.env` to git — it is in `.gitignore`
- Use app-specific passwords where available (Twitter OAuth 2.0, Bluesky app passwords)
- Browser automation runs headless in CI, headed locally for debugging

## Sources

Based on [lackeyjb/playwright-skill](https://github.com/lackeyjb/playwright-skill), [invariantlabs-ai/playwright-computer-use](https://github.com/invariantlabs-ai/playwright-computer-use), and [typefully/typefully](https://typefully.com).
