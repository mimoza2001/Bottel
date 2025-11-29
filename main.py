#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bottel - Telegram Vocabulary Bot
Main entry point for running the bot with scheduler.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.database import init_database
from src.bot import VocabularyBot
from src.scheduler import VocabularyScheduler


async def setup():
    """Initialize database and other setup tasks."""
    print("🔧 Setting up Bottel...")
    await init_database()
    print("✅ Setup complete!")


def main():
    """Main entry point."""
    print("""
    ╔═══════════════════════════════════════╗
    ║   🎓 BOTTEL - Vocabulary Coach        ║
    ║   Learn C1-C2 English from Twitter    ║
    ╚═══════════════════════════════════════╝
    """)
    
    # Check required env vars
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not bot_token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)
    
    if not gemini_key:
        print("⚠️ Warning: GEMINI_API_KEY not set - Twitter fetching won't work")
    
    # Run setup
    asyncio.run(setup())
    
    # Create and start scheduler
    scheduler = VocabularyScheduler(bot_token)
    scheduler.start()
    
    # Run bot (this blocks)
    bot = VocabularyBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        scheduler.stop()


if __name__ == "__main__":
    main()
