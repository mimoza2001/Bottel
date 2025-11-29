"""
Telegram Bot for vocabulary learning with spaced repetition.
Features:
- Sends daily vocabulary from Twitter feed
- Tracks read status with button confirmations
- Sends reminder notifications every 5 minutes until read
- Implements memory curve for spaced repetition
"""

import os
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes
)
from dotenv import load_dotenv

from src.database import (
    init_database,
    add_word,
    get_words_for_review,
    get_new_words,
    mark_word_reviewed,
    create_batch,
    mark_batch_read,
    get_unread_batches,
    update_reminder_sent,
    get_all_words_count,
    get_words_by_stage,
    get_setting,
    set_setting,
    ReviewStage
)
from src.twitter_scraper import fetch_and_extract_vocabulary

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Reminder interval in seconds (5 minutes)
REMINDER_INTERVAL = 5 * 60


class VocabularyBot:
    """Main bot class handling all vocabulary learning features."""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.reminder_task: Optional[asyncio.Task] = None
        self.chat_id: Optional[int] = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - register user and show welcome."""
        chat_id = update.effective_chat.id
        await set_setting("chat_id", str(chat_id))
        self.chat_id = chat_id
        
        welcome_msg = """🎓 *Welcome to Bottel - Your Vocabulary Coach!*

I'll help you learn advanced English vocabulary (C1-C2) from Twitter using spaced repetition.

*How it works:*
📚 I'll send you 15 new words/phrases daily
🔄 Words are reviewed based on the memory curve:
   • 24 hours → 2-3 days → 1 week → 2 weeks → 1 month
✅ Tap "I've read this" to confirm
⏰ If you don't confirm, I'll remind you every 5 minutes

*Commands:*
/words - Get today's vocabulary now
/review - Get words due for review
/stats - See your learning progress
/fetch - Fetch new words from Twitter
/help - Show this message

Ready to expand your vocabulary? Use /fetch to get started!"""
        
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """📖 *Bottel Commands*

/start - Register and see welcome
/words - Get today's vocabulary batch
/review - Get words due for review
/fetch - Fetch new vocabulary from Twitter
/stats - View your learning statistics
/add <word> - Manually add a word
/help - Show this help message

*How Reading Confirmation Works:*
When you receive words, tap "✅ I've read this" to confirm. Until you do, I'll send reminders every 5 minutes.

*Memory Curve Schedule:*
• New → Review after 24 hours
• Stage 1 → Review after 2-3 days  
• Stage 2 → Review after 1 week
• Stage 3 → Review after 2 weeks
• Stage 4 → Review after 1 month
• Mastered! 🎉"""
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def fetch_words(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fetch new vocabulary from Twitter feed."""
        await update.message.reply_text("🔄 Fetching vocabulary from Twitter... This may take a moment.")
        
        try:
            words = await fetch_and_extract_vocabulary(word_count=15)
            
            if not words:
                await update.message.reply_text(
                    "❌ Couldn't fetch words. Please check your API keys and try again."
                )
                return
            
            added_count = 0
            for word in words:
                word_id = await add_word(
                    word=word.word,
                    context=word.context,
                    definition=word.definition,
                    example=word.example
                )
                if word_id:
                    added_count += 1
            
            await update.message.reply_text(
                f"✅ Added {added_count} new words to your learning queue!\n"
                f"Use /words to see today's vocabulary."
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching words: {str(e)}")
    
    async def send_words(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send today's vocabulary batch (new words)."""
        chat_id = update.effective_chat.id
        
        # Get new words
        new_words = await get_new_words(limit=15)
        
        if not new_words:
            await update.message.reply_text(
                "📭 No new words available!\n"
                "Use /fetch to get vocabulary from Twitter, or /review for words due for review."
            )
            return
        
        # Create batch ID
        batch_id = f"new_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Format message
        message = self._format_word_batch(new_words, is_review=False)
        
        # Create read confirmation button
        keyboard = [[InlineKeyboardButton(
            "✅ I've read this", 
            callback_data=f"read:{batch_id}"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message
        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        # Record batch
        await create_batch(
            batch_id=batch_id,
            word_count=len(new_words),
            new_count=len(new_words),
            review_count=0,
            message_id=sent_msg.message_id
        )
        
        # Store word IDs for this batch in context
        context.bot_data[batch_id] = [w.id for w in new_words]
    
    async def send_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send words due for review."""
        chat_id = update.effective_chat.id
        
        # Get review words
        review_words = await get_words_for_review(limit=15)
        
        if not review_words:
            await update.message.reply_text(
                "🎉 No words due for review right now!\n"
                "Great job staying on top of your learning!"
            )
            return
        
        # Create batch ID
        batch_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Format message
        message = self._format_word_batch(review_words, is_review=True)
        
        # Create read confirmation button
        keyboard = [[InlineKeyboardButton(
            "✅ I've reviewed this", 
            callback_data=f"read:{batch_id}"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message
        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        # Record batch
        await create_batch(
            batch_id=batch_id,
            word_count=len(review_words),
            new_count=0,
            review_count=len(review_words),
            message_id=sent_msg.message_id
        )
        
        # Store word IDs for this batch
        context.bot_data[batch_id] = [w.id for w in review_words]
    
    def _format_word_batch(self, words, is_review: bool = False) -> str:
        """Format a batch of words into a nice message."""
        if is_review:
            header = "🔄 *REVIEW TIME!*\n\nThese words need reinforcement:\n"
        else:
            header = "📚 *TODAY'S VOCABULARY*\n\nNew words to learn:\n"
        
        lines = [header, "─" * 25]
        
        for i, word in enumerate(words, 1):
            stage_emoji = self._get_stage_emoji(word.review_stage)
            lines.append(f"\n*{i}. {word.word}* {stage_emoji}")
            if word.definition:
                lines.append(f"📖 {word.definition}")
            if word.example:
                lines.append(f"💬 _{word.example}_")
            if word.context:
                # Truncate long contexts
                ctx = word.context[:100] + "..." if len(word.context) > 100 else word.context
                lines.append(f"🐦 `{ctx}`")
            lines.append("")
        
        lines.append("─" * 25)
        lines.append(f"\n📊 Total: {len(words)} words")
        lines.append("👆 *Tap the button below when you've read these!*")
        
        return "\n".join(lines)
    
    def _get_stage_emoji(self, stage: ReviewStage) -> str:
        """Get emoji indicator for review stage."""
        emojis = {
            ReviewStage.NEW: "🆕",
            ReviewStage.STAGE_1: "1️⃣",
            ReviewStage.STAGE_2: "2️⃣",
            ReviewStage.STAGE_3: "3️⃣",
            ReviewStage.STAGE_4: "4️⃣",
            ReviewStage.STAGE_5: "5️⃣",
            ReviewStage.MASTERED: "🏆"
        }
        return emojis.get(stage, "📝")
    
    async def handle_read_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when user confirms they've read the words."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if not data.startswith("read:"):
            return
        
        batch_id = data.replace("read:", "")
        
        # Mark batch as read
        await mark_batch_read(batch_id)
        
        # Mark all words in batch as reviewed
        word_ids = context.bot_data.get(batch_id, [])
        for word_id in word_ids:
            await mark_word_reviewed(word_id)
        
        # Update message to show it's been read
        await query.edit_message_reply_markup(reply_markup=None)
        
        # Send confirmation
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ *Great job!* Words marked as reviewed.\n\n"
                 "I'll remind you to review them again based on the memory curve! 🧠",
            parse_mode="Markdown"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show learning statistics."""
        total_words = await get_all_words_count()
        stages = await get_words_by_stage()
        
        stats_msg = f"""📊 *Your Learning Statistics*

📚 *Total Words:* {total_words}

*Progress by Stage:*
🆕 New: {stages.get('NEW', 0)}
1️⃣ Stage 1 (24h): {stages.get('STAGE_1', 0)}
2️⃣ Stage 2 (2-3d): {stages.get('STAGE_2', 0)}
3️⃣ Stage 3 (1wk): {stages.get('STAGE_3', 0)}
4️⃣ Stage 4 (2wk): {stages.get('STAGE_4', 0)}
5️⃣ Stage 5 (1mo): {stages.get('STAGE_5', 0)}
🏆 Mastered: {stages.get('MASTERED', 0)}

Keep learning! 💪"""
        
        await update.message.reply_text(stats_msg, parse_mode="Markdown")
    
    async def add_word_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually add a word."""
        if not context.args:
            await update.message.reply_text(
                "Usage: /add <word or phrase>\n"
                "Example: /add beat around the bush"
            )
            return
        
        word = " ".join(context.args)
        word_id = await add_word(word=word)
        
        if word_id:
            await update.message.reply_text(f"✅ Added '{word}' to your learning queue!")
        else:
            await update.message.reply_text(f"⚠️ '{word}' is already in your vocabulary!")
    
    async def reminder_loop(self, app: Application):
        """Background task to send reminders for unread batches."""
        while True:
            try:
                await asyncio.sleep(REMINDER_INTERVAL)
                
                chat_id = await get_setting("chat_id")
                if not chat_id:
                    continue
                
                unread_batches = await get_unread_batches()
                
                for batch_id, message_id, sent_at, reminder_count in unread_batches:
                    # Check if enough time has passed since sending
                    time_since_sent = datetime.now() - sent_at
                    if time_since_sent.total_seconds() < REMINDER_INTERVAL:
                        continue
                    
                    # Send reminder
                    reminder_msg = (
                        f"⏰ *Reminder #{reminder_count + 1}*\n\n"
                        f"You haven't confirmed reading your vocabulary yet!\n"
                        f"Please review the words above and tap '✅ I've read this'"
                    )
                    
                    await app.bot.send_message(
                        chat_id=int(chat_id),
                        text=reminder_msg,
                        parse_mode="Markdown",
                        reply_to_message_id=message_id
                    )
                    
                    await update_reminder_sent(batch_id)
                    print(f"📢 Sent reminder #{reminder_count + 1} for batch {batch_id}")
                    
            except Exception as e:
                print(f"⚠️ Reminder loop error: {e}")
    
    async def post_init(self, app: Application):
        """Post-initialization hook to start background tasks."""
        # Start reminder loop
        self.reminder_task = asyncio.create_task(self.reminder_loop(app))
        print("✅ Reminder loop started")
    
    def run(self):
        """Run the bot."""
        print("🚀 Starting Bottel...")
        
        # Build application
        self.application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(self.post_init)
            .build()
        )
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("fetch", self.fetch_words))
        self.application.add_handler(CommandHandler("words", self.send_words))
        self.application.add_handler(CommandHandler("review", self.send_review))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("add", self.add_word_command))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_read_confirmation, 
            pattern="^read:"
        ))
        
        # Run bot
        print("🤖 Bot is running! Press Ctrl+C to stop.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


async def main():
    """Main entry point."""
    await init_database()
    bot = VocabularyBot()
    bot.run()


if __name__ == "__main__":
    asyncio.run(main())
