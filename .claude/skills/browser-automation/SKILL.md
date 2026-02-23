---
name: browser-automation
description: >
  Browser automation for social media posting and web interaction. Use this skill
  when the user wants to: post on Twitter/X, Instagram, LinkedIn, Telegram,
  TikTok, or other social platforms; automate form filling; scrape web content;
  take screenshots; click buttons; fill login forms; or perform any browser-based
  task. Uses Playwright for reliable cross-browser automation.
tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Browser Automation Skill — Social Media Posting

You are a browser automation specialist. When invoked, write and execute
Playwright scripts to automate browser tasks, with a focus on social media
posting on behalf of the user.

## Setup

```bash
pip install playwright
playwright install chromium   # or: playwright install --with-deps chromium
```

Or with Node.js:
```bash
npm install playwright
npx playwright install chromium
```

## Core Pattern (Python)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)   # headless=True for background
    context = browser.new_context(
        storage_state='auth/session.json'          # reuse saved login session
    )
    page = context.new_page()
    page.goto('https://example.com')
    page.screenshot(path='screenshot.png')
    browser.close()
```

## Session Persistence (avoid logging in every time)

### Save session (run once manually):
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://twitter.com/login')
    input('Log in manually in the browser, then press Enter...')
    context.storage_state(path='auth/twitter_session.json')
    browser.close()
    print('Session saved to auth/twitter_session.json')
```

### Use saved session:
```python
context = browser.new_context(storage_state='auth/twitter_session.json')
```

## Twitter / X — Post a Tweet

```python
from playwright.sync_api import sync_playwright

def post_tweet(text: str, session_file='auth/twitter_session.json'):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx  = browser.new_context(storage_state=session_file)
        page = ctx.new_page()
        page.goto('https://x.com/home')
        page.wait_for_load_state('networkidle')

        # Click the tweet compose box
        page.click('[data-testid="tweetTextarea_0"]')
        page.type('[data-testid="tweetTextarea_0"]', text, delay=50)

        # Click the Post button
        page.click('[data-testid="tweetButtonInline"]')
        page.wait_for_timeout(2000)   # wait for submission
        browser.close()
        print(f'Tweeted: {text}')
```

## Instagram — Post a Photo Caption

```python
def post_instagram(caption: str, image_path: str, session_file='auth/instagram_session.json'):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Instagram needs headful
        ctx  = browser.new_context(storage_state=session_file)
        page = ctx.new_page()
        page.goto('https://www.instagram.com')
        page.wait_for_load_state('networkidle')

        # New post
        page.click('svg[aria-label="New post"]')
        page.set_input_files('input[type="file"]', image_path)
        page.click('button:has-text("Next")')
        page.click('button:has-text("Next")')

        # Caption
        page.fill('textarea[aria-label="Write a caption..."]', caption)
        page.click('button:has-text("Share")')
        page.wait_for_timeout(3000)
        browser.close()
```

## LinkedIn — Post an Update

```python
def post_linkedin(text: str, session_file='auth/linkedin_session.json'):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx  = browser.new_context(storage_state=session_file)
        page = ctx.new_page()
        page.goto('https://www.linkedin.com/feed/')
        page.wait_for_load_state('networkidle')

        page.click('button.share-box-feed-entry__trigger')
        page.wait_for_selector('.ql-editor')
        page.click('.ql-editor')
        page.keyboard.type(text, delay=30)
        page.click('button.share-actions__primary-action')
        page.wait_for_timeout(2000)
        browser.close()
```

## Telegram — Send Message via Bot API (no browser needed)

For Telegram, use the Bot API directly instead of browser automation:

```python
import requests, os

def send_telegram(text: str):
    token   = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    r = requests.post(url, json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'})
    r.raise_for_status()
    return r.json()
```

## Utility Functions

```python
# Take a full-page screenshot
page.screenshot(path='screenshot.png', full_page=True)

# Wait for element
page.wait_for_selector('.my-class', timeout=10000)

# Extract text
text = page.text_content('h1')

# Fill a form
page.fill('input[name="username"]', 'myuser')
page.fill('input[name="password"]', 'mypass')
page.click('button[type="submit"]')

# Handle popups / modals
page.on('dialog', lambda d: d.accept())
```

## Scheduled Posting

Use APScheduler to post at specific times:

```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=9, minute=0)   # 9 AM every day
def morning_post():
    post_tweet('Good morning! Here is the BTC price: ...')

scheduler.start()
```

## Error Handling

```python
from playwright.sync_api import TimeoutError as PWTimeout

try:
    page.click('button.submit', timeout=5000)
except PWTimeout:
    page.screenshot(path='error_state.png')
    raise RuntimeError('Submit button not found — see error_state.png')
```

## Templates

- `templates/twitter_post.txt` — Twitter post template
- `templates/linkedin_post.txt` — LinkedIn post template
- `templates/instagram_caption.txt` — Instagram caption template

## Security Notes

1. Store sessions in `auth/` — add `auth/` to `.gitignore`.
2. Never commit session files or `.env` to git.
3. Use `headless=False` when debugging; `headless=True` in production.
4. Respect platform rate limits — add `wait_for_timeout()` delays between posts.
