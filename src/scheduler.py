"""
Scheduler module for automatic vocabulary fetching and sending.
Handles:
- Daily vocabulary fetch from Twitter
- Sending review reminders based on memory curve
- Periodic reminders for unread batches
"""

import asyncio
from datetime import datetime, time
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import uuid

from src.database import (
    get_setting,
    get_new_words,
    get_words_for_review,
    create_batch,
    get_unread_batches,
    update_reminder_sent,
    mark_word_reviewed,
    add_word,
    ReviewStage
)
from src.twitter_scraper import fetch_and_extract_vocabulary


class VocabularyScheduler:
    """Handles scheduled tasks for the vocabulary bot."""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.scheduler = AsyncIOScheduler()
        self.word_batch_data = {}  # Store batch -> word_ids mapping
    
    def _format_word_batch(self, words, is_review: bool = False) -> str:
        """Format a batch of words into a nice message."""
        if is_review:
            header = "🔄 *REVIEW TIME!*\n\nThese words need reinforcement:\n"
        else:
            header = "📚 *TODAY'S VOCABULARY*\n\nNew words to learn:\n"
        
        stage_emojis = {
            ReviewStage.NEW: "🆕",
            ReviewStage.STAGE_1: "1️⃣",
            ReviewStage.STAGE_2: "2️⃣",
            ReviewStage.STAGE_3: "3️⃣",
            ReviewStage.STAGE_4: "4️⃣",
            ReviewStage.STAGE_5: "5️⃣",
            ReviewStage.MASTERED: "🏆"
        }
        
        lines = [header, "─" * 25]
        
        for i, word in enumerate(words, 1):
            stage_emoji = stage_emojis.get(word.review_stage, "📝")
            lines.append(f"\n*{i}. {word.word}* {stage_emoji}")
            if word.definition:
                lines.append(f"📖 {word.definition}")
            if word.example:
                lines.append(f"💬 _{word.example}_")
            if word.context:
                ctx = word.context[:100] + "..." if len(word.context) > 100 else word.context
                lines.append(f"🐦 `{ctx}`")
            lines.append("")
        
        lines.append("─" * 25)
        lines.append(f"\n📊 Total: {len(words)} words")
        lines.append("👆 *Tap the button below when you've read these!*")
        
        return "\n".join(lines)
    
    async def fetch_daily_vocabulary(self):
        """Fetch new vocabulary from Twitter - runs daily."""
        print(f"📅 [{datetime.now()}] Running daily vocabulary fetch...")
        
        try:
            words = await fetch_and_extract_vocabulary(word_count=15)
            
            if words:
                added = 0
                for word in words:
                    word_id = await add_word(
                        word=word.word,
                        context=word.context,
                        definition=word.definition,
                        example=word.example
                    )
                    if word_id:
                        added += 1
                
                print(f"✅ Added {added} new words from Twitter")
            else:
                print("⚠️ No words fetched from Twitter")
                
        except Exception as e:
            print(f"❌ Error fetching vocabulary: {e}")
    
    async def send_daily_words(self):
        """Send daily vocabulary to user."""
        chat_id = await get_setting("chat_id")
        if not chat_id:
            print("⚠️ No chat_id set - user needs to /start the bot first")
            return
        
        print(f"📤 [{datetime.now()}] Sending daily vocabulary...")
        
        # Get new words
        new_words = await get_new_words(limit=15)
        
        if not new_words:
            print("📭 No new words to send")
            return
        
        # Create batch
        batch_id = f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Format and send
        message = self._format_word_batch(new_words, is_review=False)
        
        keyboard = [[InlineKeyboardButton(
            "✅ I've read this",
            callback_data=f"read:{batch_id}"
        )]]
        
        try:
            sent_msg = await self.bot.send_message(
                chat_id=int(chat_id),
                text=message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            await create_batch(
                batch_id=batch_id,
                word_count=len(new_words),
                new_count=len(new_words),
                review_count=0,
                message_id=sent_msg.message_id
            )
            
            # Store word IDs
            self.word_batch_data[batch_id] = [w.id for w in new_words]
            
            print(f"✅ Sent {len(new_words)} words (batch: {batch_id})")
            
        except Exception as e:
            print(f"❌ Error sending words: {e}")
    
    async def send_review_words(self):
        """Send words due for review based on memory curve."""
        chat_id = await get_setting("chat_id")
        if not chat_id:
            return
        
        print(f"🔄 [{datetime.now()}] Checking for review words...")
        
        review_words = await get_words_for_review(limit=15)
        
        if not review_words:
            print("✨ No words due for review")
            return
        
        batch_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        message = self._format_word_batch(review_words, is_review=True)
        
        keyboard = [[InlineKeyboardButton(
            "✅ I've reviewed this",
            callback_data=f"read:{batch_id}"
        )]]
        
        try:
            sent_msg = await self.bot.send_message(
                chat_id=int(chat_id),
                text=message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            await create_batch(
                batch_id=batch_id,
                word_count=len(review_words),
                new_count=0,
                review_count=len(review_words),
                message_id=sent_msg.message_id
            )
            
            self.word_batch_data[batch_id] = [w.id for w in review_words]
            
            print(f"✅ Sent {len(review_words)} review words")
            
        except Exception as e:
            print(f"❌ Error sending review: {e}")
    
    async def check_unread_reminders(self):
        """Send reminders for unread batches every 5 minutes."""
        chat_id = await get_setting("chat_id")
        if not chat_id:
            return
        
        unread_batches = await get_unread_batches()
        
        for batch_id, message_id, sent_at, reminder_count in unread_batches:
            time_since_sent = datetime.now() - sent_at
            
            # Only remind if at least 5 minutes have passed
            if time_since_sent.total_seconds() < 300:
                continue
            
            try:
                reminder_msg = (
                    f"⏰ *Reminder #{reminder_count + 1}*\n\n"
                    f"You haven't confirmed reading your vocabulary!\n"
                    f"Please review the words above and tap the button."
                )
                
                await self.bot.send_message(
                    chat_id=int(chat_id),
                    text=reminder_msg,
                    parse_mode="Markdown",
                    reply_to_message_id=message_id
                )
                
                await update_reminder_sent(batch_id)
                print(f"📢 Reminder sent for batch {batch_id}")
                
            except Exception as e:
                print(f"⚠️ Couldn't send reminder: {e}")
    
    def start(self):
        """Start the scheduler with all jobs."""
        # Fetch vocabulary daily at 6:30 AM (before sending at 7 AM)
        self.scheduler.add_job(
            self.fetch_daily_vocabulary,
            CronTrigger(hour=6, minute=30),
            id="daily_fetch",
            name="Daily vocabulary fetch"
        )
        
        # Send daily words at 7 AM
        self.scheduler.add_job(
            self.send_daily_words,
            CronTrigger(hour=7, minute=0),
            id="daily_send",
            name="Daily vocabulary send"
        )
        
        # Check for reviews every hour
        self.scheduler.add_job(
            self.send_review_words,
            CronTrigger(minute=0),  # Every hour on the hour
            id="hourly_review",
            name="Hourly review check"
        )
        
        # Check for unread reminders every 5 minutes
        self.scheduler.add_job(
            self.check_unread_reminders,
            IntervalTrigger(minutes=5),
            id="reminder_check",
            name="Unread reminder check"
        )
        
        self.scheduler.start()
        print("📅 Scheduler started with jobs:")
        print("   • Daily fetch: 6:30 AM")
        print("   • Daily send: 7:00 AM")
        print("   • Review check: Every hour")
        print("   • Reminder check: Every 5 minutes")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        print("📅 Scheduler stopped")
