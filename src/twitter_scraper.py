"""
Twitter scraper module using Playwright for browser automation
and Gemini API for C1-C2 vocabulary extraction.
"""

import os
import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")


@dataclass
class ExtractedWord:
    word: str
    definition: str
    example: str
    context: str  # Original tweet
    difficulty: str  # C1 or C2


class GeminiVocabularyExtractor:
    """Uses Gemini to extract C1-C2 vocabulary from text."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def extract_vocabulary(self, tweets: List[str], count: int = 15) -> List[ExtractedWord]:
        """
        Extract C1-C2 level words/phrases from tweets.
        
        Args:
            tweets: List of tweet texts
            count: Number of words/phrases to extract
            
        Returns:
            List of ExtractedWord objects
        """
        combined_text = "\n---\n".join(tweets)
        
        prompt = f"""Analyze these tweets and extract exactly {count} C1-C2 level English vocabulary words or phrases.

TWEETS:
{combined_text}

---

For each word/phrase, provide:
1. The word or phrase (exactly as useful for learning)
2. A clear, concise definition
3. An example sentence showing proper usage
4. The original tweet context it came from
5. Difficulty level (C1 or C2)

IMPORTANT CRITERIA:
- Focus on ADVANCED vocabulary (C1-C2 level) - words/phrases that educated native speakers use
- Include idioms, phrasal verbs, collocations, and sophisticated single words
- Avoid basic words (A1-B2 level)
- Prefer words with practical daily usage for an advanced learner
- Include the exact phrase/collocation when relevant (e.g., "drive home a point" not just "drive")

Return ONLY valid JSON array with this exact format:
[
  {{
    "word": "word or phrase",
    "definition": "clear definition",
    "example": "example sentence",
    "context": "original tweet excerpt",
    "difficulty": "C1 or C2"
  }}
]

Return ONLY the JSON array, no other text."""

        try:
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            
            # Parse JSON from response
            text = response.text.strip()
            # Remove markdown code blocks if present
            if text.startswith("```"):
                text = re.sub(r'^```\w*\n?', '', text)
                text = re.sub(r'\n?```$', '', text)
            
            words_data = json.loads(text)
            
            return [
                ExtractedWord(
                    word=w["word"],
                    definition=w["definition"],
                    example=w["example"],
                    context=w["context"],
                    difficulty=w["difficulty"]
                )
                for w in words_data[:count]
            ]
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Gemini response: {e}")
            print(f"Response was: {response.text[:500]}")
            return []
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return []


class TwitterScraper:
    """
    Scrapes Twitter feed using multiple methods:
    1. Nitter (public Twitter frontend)
    2. Direct browser automation with Playwright
    """
    
    def __init__(self):
        self.nitter_instances = [
            "https://nitter.privacydev.net",
            "https://nitter.poast.org", 
            "https://nitter.1d4.us",
            "https://nitter.kavin.rocks",
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    async def get_home_timeline_nitter(self, username: str) -> List[str]:
        """
        Try to get tweets from users that the account follows via Nitter.
        Note: Nitter shows public profiles, not personalized home feed.
        This gets tweets from accounts we specify.
        """
        tweets = []
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for instance in self.nitter_instances:
                try:
                    # Get the user's following list or specific accounts
                    url = f"{instance}/{username}"
                    response = await client.get(url, headers=self.headers)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'lxml')
                        tweet_elements = soup.select('.timeline-item .tweet-content')
                        
                        for tweet_el in tweet_elements[:50]:  # Get up to 50 tweets
                            text = tweet_el.get_text(strip=True)
                            if text and len(text) > 20:  # Filter very short tweets
                                tweets.append(text)
                        
                        if tweets:
                            print(f"✅ Fetched {len(tweets)} tweets from {instance}")
                            return tweets
                            
                except Exception as e:
                    print(f"⚠️ Nitter instance {instance} failed: {e}")
                    continue
        
        return tweets
    
    async def get_tweets_from_accounts(self, accounts: List[str], per_account: int = 10) -> List[str]:
        """
        Get tweets from specific Twitter accounts via Nitter.
        
        Args:
            accounts: List of Twitter usernames to scrape
            per_account: Number of tweets per account
        """
        all_tweets = []
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for account in accounts:
                for instance in self.nitter_instances:
                    try:
                        url = f"{instance}/{account}"
                        response = await client.get(url, headers=self.headers)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'lxml')
                            tweet_elements = soup.select('.timeline-item .tweet-content')
                            
                            account_tweets = []
                            for tweet_el in tweet_elements[:per_account]:
                                text = tweet_el.get_text(strip=True)
                                if text and len(text) > 30:
                                    account_tweets.append(text)
                            
                            if account_tweets:
                                all_tweets.extend(account_tweets)
                                print(f"✅ Got {len(account_tweets)} tweets from @{account}")
                                break  # Move to next account
                                
                    except Exception as e:
                        continue
                        
                await asyncio.sleep(1)  # Rate limiting
        
        return all_tweets


class TwitterPlaywrightScraper:
    """
    Advanced Twitter scraper using Playwright for authenticated access.
    This can access the actual home feed.
    """
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.browser = None
        self.context = None
        self.page = None
    
    async def initialize(self):
        """Initialize Playwright browser."""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self.page = await self.context.new_page()
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Playwright: {e}")
            return False
    
    async def login(self) -> bool:
        """Login to Twitter."""
        try:
            await self.page.goto("https://twitter.com/login", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Enter username
            username_input = await self.page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            await username_input.fill(self.username)
            await self.page.click('text=Next')
            await asyncio.sleep(2)
            
            # Enter password
            password_input = await self.page.wait_for_selector('input[type="password"]', timeout=10000)
            await password_input.fill(self.password)
            await self.page.click('text=Log in')
            await asyncio.sleep(5)
            
            # Check if logged in
            if "home" in self.page.url:
                print("✅ Successfully logged into Twitter")
                return True
            else:
                print("⚠️ Login may have failed, checking...")
                return True  # Try anyway
                
        except Exception as e:
            print(f"❌ Twitter login failed: {e}")
            return False
    
    async def get_home_feed(self, scroll_count: int = 3) -> List[str]:
        """Get tweets from home feed."""
        tweets = []
        
        try:
            await self.page.goto("https://twitter.com/home", wait_until="networkidle")
            await asyncio.sleep(3)
            
            for _ in range(scroll_count):
                # Extract tweet texts
                tweet_elements = await self.page.query_selector_all('[data-testid="tweetText"]')
                
                for el in tweet_elements:
                    text = await el.inner_text()
                    if text and len(text) > 30 and text not in tweets:
                        tweets.append(text)
                
                # Scroll down
                await self.page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)
            
            print(f"✅ Extracted {len(tweets)} tweets from home feed")
            
        except Exception as e:
            print(f"❌ Failed to get home feed: {e}")
        
        return tweets
    
    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()


async def fetch_and_extract_vocabulary(
    accounts: List[str] = None,
    word_count: int = 15,
    use_playwright: bool = False
) -> List[ExtractedWord]:
    """
    Main function to fetch tweets and extract vocabulary.
    
    Args:
        accounts: Optional list of Twitter accounts to follow for vocabulary
        word_count: Number of words to extract
        use_playwright: Whether to use authenticated Playwright scraping
        
    Returns:
        List of extracted vocabulary words
    """
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not set!")
        return []
    
    tweets = []
    
    # Default accounts with rich C1-C2 vocabulary (news, literary, academic)
    if not accounts:
        accounts = [
            "TheEconomist",
            "nikitonsky", 
            "guardian",
            "NYTimes",
            "baborschka",
            "TheAtlantic",
            "NewYorker",
            "NPR",
            "BBC",
            "FT"
        ]
    
    if use_playwright and TWITTER_USERNAME and TWITTER_PASSWORD:
        # Try authenticated scraping first
        scraper = TwitterPlaywrightScraper(TWITTER_USERNAME, TWITTER_PASSWORD)
        if await scraper.initialize():
            if await scraper.login():
                tweets = await scraper.get_home_feed()
            await scraper.close()
    
    # Fall back to Nitter if needed
    if not tweets:
        scraper = TwitterScraper()
        tweets = await scraper.get_tweets_from_accounts(accounts, per_account=15)
    
    if not tweets:
        print("❌ No tweets fetched!")
        return []
    
    print(f"📝 Processing {len(tweets)} tweets with Gemini...")
    
    # Extract vocabulary using Gemini
    extractor = GeminiVocabularyExtractor(GEMINI_API_KEY)
    words = await extractor.extract_vocabulary(tweets, word_count)
    
    print(f"✅ Extracted {len(words)} vocabulary words")
    return words


# CLI test
if __name__ == "__main__":
    async def test():
        words = await fetch_and_extract_vocabulary(word_count=5)
        for w in words:
            print(f"\n📚 {w.word} ({w.difficulty})")
            print(f"   Definition: {w.definition}")
            print(f"   Example: {w.example}")
    
    asyncio.run(test())
