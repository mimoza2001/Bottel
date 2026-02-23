#!/usr/bin/env python3
"""
Social media posting script.
Usage:
  python post_social.py --platform twitter --message "Hello world!"
  python post_social.py --platform telegram --message "Trade alert: BTC up 5%"
  python post_social.py --save-session twitter   # run once to save login session
"""
import argparse
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
AUTH_DIR = Path(__file__).parent.parent / 'auth'
AUTH_DIR.mkdir(exist_ok=True)


def save_session(platform: str):
    """Interactively save a browser session for a platform."""
    from playwright.sync_api import sync_playwright

    urls = {
        'twitter':   'https://x.com/login',
        'instagram': 'https://www.instagram.com/accounts/login/',
        'linkedin':  'https://www.linkedin.com/login',
    }
    if platform not in urls:
        print(f'No session-save support for: {platform}')
        sys.exit(1)

    session_file = AUTH_DIR / f'{platform}_session.json'
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(urls[platform])
        input(f'\nLog into {platform} in the browser window, then press Enter here...')
        context.storage_state(path=str(session_file))
        browser.close()
    print(f'Session saved to {session_file}')


def post_twitter(message: str):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    session_file = AUTH_DIR / 'twitter_session.json'
    if not session_file.exists():
        print('No Twitter session found. Run: python post_social.py --save-session twitter')
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx  = browser.new_context(storage_state=str(session_file))
        page = ctx.new_page()
        try:
            page.goto('https://x.com/home')
            page.wait_for_load_state('networkidle', timeout=15000)
            page.click('[data-testid="tweetTextarea_0"]', timeout=8000)
            page.type('[data-testid="tweetTextarea_0"]', message, delay=40)
            page.click('[data-testid="tweetButtonInline"]', timeout=8000)
            page.wait_for_timeout(2500)
            print(f'[Twitter] Posted: {message[:60]}...')
        except PWTimeout as e:
            page.screenshot(path=str(AUTH_DIR / 'twitter_error.png'))
            raise RuntimeError(f'Twitter post failed: {e}')
        finally:
            browser.close()


def post_linkedin(message: str):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    session_file = AUTH_DIR / 'linkedin_session.json'
    if not session_file.exists():
        print('No LinkedIn session found. Run: python post_social.py --save-session linkedin')
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx  = browser.new_context(storage_state=str(session_file))
        page = ctx.new_page()
        try:
            page.goto('https://www.linkedin.com/feed/')
            page.wait_for_load_state('networkidle', timeout=15000)
            page.click('button.share-box-feed-entry__trigger', timeout=8000)
            page.wait_for_selector('.ql-editor', timeout=8000)
            page.click('.ql-editor')
            page.keyboard.type(message, delay=30)
            page.click('button.share-actions__primary-action', timeout=8000)
            page.wait_for_timeout(2500)
            print(f'[LinkedIn] Posted: {message[:60]}...')
        except PWTimeout as e:
            page.screenshot(path=str(AUTH_DIR / 'linkedin_error.png'))
            raise RuntimeError(f'LinkedIn post failed: {e}')
        finally:
            browser.close()


def post_telegram(message: str):
    token   = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print('Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env')
        sys.exit(1)

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    r = requests.post(url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'})
    r.raise_for_status()
    print(f'[Telegram] Sent: {message[:60]}...')


PLATFORMS = {
    'twitter':  post_twitter,
    'linkedin': post_linkedin,
    'telegram': post_telegram,
}


def main():
    parser = argparse.ArgumentParser(description='Post to social media')
    parser.add_argument('--platform', choices=list(PLATFORMS.keys()), help='Target platform')
    parser.add_argument('--message', help='Content to post')
    parser.add_argument('--save-session', metavar='PLATFORM',
                        help='Save browser session for a platform (run once)')
    args = parser.parse_args()

    if args.save_session:
        save_session(args.save_session)
        return

    if not args.platform or not args.message:
        parser.error('--platform and --message are required (or use --save-session)')

    PLATFORMS[args.platform](args.message)


if __name__ == '__main__':
    main()
