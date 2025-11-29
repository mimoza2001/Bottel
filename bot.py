"""
Telegram Vocabulary Bot with Spaced Repetition
Sends daily vocabulary and uses memory curve for optimal retention.
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import database as db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Scheduler for notifications
scheduler = AsyncIOScheduler()

# Store application reference for scheduler
app_reference = None


# ============== Helper Functions ==============

def format_word_message(words: List[tuple], is_review: bool = False) -> str:
    """Format words into a nice message."""
    if is_review:
        header = "🔄 **REVIEW TIME!**\n\nTime to review these words:\n\n"
    else:
        header = "📚 **NEW VOCABULARY**\n\nHere are your new words for today:\n\n"
    
    message = header
    for i, word_data in enumerate(words, 1):
        if len(word_data) >= 6:  # Review format with schedule info
            _, word_id, level, word, definition, example = word_data[:6]
        else:  # New word format
            word_id, word, definition, example, source = word_data[:5]
        
        message += f"**{i}. {word}**\n"
        if definition:
            message += f"   📖 {definition}\n"
        if example:
            message += f"   💬 _{example}_\n"
        message += "\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━\n"
    message += "✅ Press the button below when you've read them!"
    
    return message


def get_acknowledgment_keyboard(batch_id: int, is_review: bool = False) -> InlineKeyboardMarkup:
    """Create acknowledgment keyboard."""
    callback_data = f"ack_review_{batch_id}" if is_review else f"ack_new_{batch_id}"
    keyboard = [
        [InlineKeyboardButton("✅ I've read them!", callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============== Command Handlers ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    
    # Register user
    user_id = await db.add_user(chat_id, username)
    
    welcome_msg = """
🎓 **Welcome to Advanced English Vocabulary Bot!**

I'll help you learn C1-C2 level English vocabulary using the **spaced repetition** technique (memory curve).

**How it works:**
1️⃣ I'll send you 15 new words/phrases daily
2️⃣ You press "I've read them" to acknowledge
3️⃣ If you don't read, I'll remind you every 5 minutes
4️⃣ Words will be reviewed using the memory curve:
   • 24 hours later
   • 3 days later
   • 7 days later
   • 14 days later
   • 30 days later
   • 90 days later

**Commands:**
/start - Show this message
/words - Get today's words now
/review - Get words due for review
/add - Add new words (format: word | definition | example)
/stats - View your learning statistics
/list - List all words in database
/help - Show help

Let's start learning! 📖
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_msg = """
📚 **Vocabulary Bot Help**

**Commands:**
• `/start` - Welcome message and registration
• `/words` - Get your daily new words
• `/review` - Get words due for review
• `/add word | definition | example` - Add a new word
• `/stats` - View your learning statistics
• `/list` - List all words in database
• `/help` - Show this help message

**Adding Words:**
You can add words in two ways:

1️⃣ Single word:
`/add ubiquitous | present everywhere | Smartphones are ubiquitous nowadays`

2️⃣ Multiple words (one per line):
```
/add 
ephemeral | lasting briefly | Fame is ephemeral
juxtapose | place side by side | The artist juxtaposed light and dark
```

**Memory Curve:**
Words are reviewed at increasing intervals:
• 24 hours → 3 days → 7 days → 14 days → 30 days → 90 days

**Tips:**
• Read your words carefully when they arrive
• Press the acknowledgment button after reading
• Don't ignore the reminders - they help you learn!
"""
    await update.message.reply_text(help_msg, parse_mode='Markdown')


async def words_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /words command - send new daily words."""
    chat_id = update.effective_chat.id
    user = await db.get_user_by_chat_id(chat_id)
    
    if not user:
        await update.message.reply_text("Please /start first!")
        return
    
    user_id = user[0]
    
    # Check if there's an unacknowledged batch
    unacked = await db.get_unacknowledged_batch(user_id)
    if unacked:
        await update.message.reply_text(
            "⚠️ You haven't acknowledged your previous words yet!\n"
            "Please read them and press the button first."
        )
        return
    
    # Get new words
    new_words = await db.get_unscheduled_words(user_id, limit=15)
    
    if not new_words:
        await update.message.reply_text(
            "📭 No new words available!\n\n"
            "Add more words using /add command or check /review for words to review."
        )
        return
    
    # Schedule these words for the user
    word_ids = [w[0] for w in new_words]
    await db.schedule_words_for_user(user_id, word_ids)
    
    # Create daily batch
    batch_id = await db.create_daily_batch(user_id, word_ids)
    
    # Add pending notification
    await db.add_pending_notification(user_id, batch_id, "new_words")
    
    # Send words
    message = format_word_message(new_words, is_review=False)
    keyboard = get_acknowledgment_keyboard(batch_id, is_review=False)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=keyboard)


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /review command - send words due for review."""
    chat_id = update.effective_chat.id
    user = await db.get_user_by_chat_id(chat_id)
    
    if not user:
        await update.message.reply_text("Please /start first!")
        return
    
    user_id = user[0]
    
    # Get words due for review
    due_words = await db.get_words_due_for_review(user_id)
    
    if not due_words:
        await update.message.reply_text(
            "🎉 No words due for review right now!\n\n"
            "Check back later or get new words with /words"
        )
        return
    
    # Mark as sent
    schedule_ids = [w[0] for w in due_words]
    await db.mark_review_sent(schedule_ids)
    
    # Create batch for tracking
    word_ids = [w[1] for w in due_words]
    batch_id = await db.create_daily_batch(user_id, word_ids)
    
    # Add pending notification
    await db.add_pending_notification(user_id, batch_id, "review")
    
    # Store schedule_ids in context for acknowledgment
    context.user_data[f'review_batch_{batch_id}'] = schedule_ids
    
    # Send words
    message = format_word_message(due_words, is_review=True)
    keyboard = get_acknowledgment_keyboard(batch_id, is_review=True)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=keyboard)


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command - add new words."""
    if not context.args and not update.message.text.strip().replace('/add', '').strip():
        await update.message.reply_text(
            "📝 **How to add words:**\n\n"
            "Single word:\n"
            "`/add ubiquitous | present everywhere | Smartphones are ubiquitous`\n\n"
            "Multiple words (one per line):\n"
            "```\n/add\nephemeral | brief | Fame is ephemeral\njuxtapose | compare | Art juxtaposes ideas\n```",
            parse_mode='Markdown'
        )
        return
    
    # Get the text after /add
    text = update.message.text.replace('/add', '').strip()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    added_words = []
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 1:
            word = parts[0]
            definition = parts[1] if len(parts) > 1 else None
            example = parts[2] if len(parts) > 2 else None
            
            word_id = await db.add_word(word, definition, example, source="manual")
            if word_id:
                added_words.append(word)
    
    if added_words:
        count = len(added_words)
        total = await db.get_word_count()
        await update.message.reply_text(
            f"✅ Added {count} word(s)!\n\n"
            f"Words: {', '.join(added_words)}\n\n"
            f"📊 Total words in database: {total}\n\n"
            f"Use /words to start learning them!"
        )
    else:
        await update.message.reply_text("❌ No words were added. Check your format.")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show learning statistics."""
    chat_id = update.effective_chat.id
    user = await db.get_user_by_chat_id(chat_id)
    
    if not user:
        await update.message.reply_text("Please /start first!")
        return
    
    user_id = user[0]
    stats = await db.get_user_stats(user_id)
    total_words = await db.get_word_count()
    
    msg = f"""
📊 **Your Learning Statistics**

📚 Total words in database: {total_words}
📖 Words you're learning: {stats['total_learned']}
🏆 Words mastered: {stats['mastered']}
🔄 Due for review: {stats['due_for_review']}

**Memory Curve Intervals:**
Level 1: 24 hours
Level 2: 3 days
Level 3: 7 days
Level 4: 14 days
Level 5: 30 days
Level 6: 90 days (Mastered!)

Keep learning! 💪
"""
    await update.message.reply_text(msg, parse_mode='Markdown')


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command - list all words."""
    words = await db.get_all_words()
    
    if not words:
        await update.message.reply_text("📭 No words in database yet! Use /add to add some.")
        return
    
    # Split into chunks to avoid message length limits
    chunk_size = 20
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    
    for i, chunk in enumerate(chunks):
        msg = f"📚 **Word List** (Page {i+1}/{len(chunks)})\n\n"
        for word in chunk:
            word_id, word_text, definition, example, source = word
            msg += f"• **{word_text}**"
            if definition:
                msg += f" - {definition}"
            msg += "\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        if len(chunks) > 1:
            await asyncio.sleep(0.5)  # Avoid rate limiting


# ============== Callback Handlers ==============

async def acknowledgment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle acknowledgment button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = update.effective_chat.id
    user = await db.get_user_by_chat_id(chat_id)
    
    if not user:
        await query.edit_message_text("Error: User not found. Please /start again.")
        return
    
    user_id = user[0]
    
    if data.startswith("ack_new_") or data.startswith("ack_review_"):
        batch_id = int(data.split("_")[-1])
        is_review = data.startswith("ack_review_")
        
        # Mark batch as acknowledged
        await db.acknowledge_batch(batch_id)
        
        # Remove pending notification
        await db.remove_pending_notification(batch_id)
        
        # If it's a review, update the review schedule
        if is_review and f'review_batch_{batch_id}' in context.user_data:
            schedule_ids = context.user_data[f'review_batch_{batch_id}']
            for sid in schedule_ids:
                await db.acknowledge_review(sid)
            del context.user_data[f'review_batch_{batch_id}']
        
        # Update message
        original_text = query.message.text
        new_text = original_text.replace(
            "✅ Press the button below when you've read them!",
            "✅ **ACKNOWLEDGED!** Great job! 🎉"
        )
        
        await query.edit_message_text(new_text, parse_mode='Markdown')
        
        # Send confirmation
        if is_review:
            await context.bot.send_message(
                chat_id,
                "🎉 Review complete! These words will be reviewed again based on the memory curve."
            )
        else:
            await context.bot.send_message(
                chat_id,
                "🎉 Great! These words are now in your learning queue.\n"
                "They'll come back for review in 24 hours!"
            )


# ============== Scheduled Tasks ==============

async def send_reminder_notifications():
    """Send reminder notifications every 5 minutes for unread messages."""
    if not app_reference:
        return
    
    pending = await db.get_pending_notifications()
    
    for notification in pending:
        notif_id, user_id, batch_id, msg_type, last_reminder, reminder_count, chat_id = notification
        
        # Check if 5 minutes have passed since last reminder
        if last_reminder:
            last_dt = datetime.fromisoformat(last_reminder)
            if datetime.now() - last_dt < timedelta(minutes=5):
                continue
        
        # Send reminder
        reminder_msg = (
            "⏰ **REMINDER!**\n\n"
            "You haven't acknowledged your vocabulary words yet!\n\n"
            "Please scroll up and press the '✅ I've read them!' button.\n\n"
            f"_Reminder #{reminder_count + 1}_"
        )
        
        try:
            await app_reference.bot.send_message(
                chat_id,
                reminder_msg,
                parse_mode='Markdown'
            )
            await db.update_notification_reminder(notif_id)
            logger.info(f"Sent reminder #{reminder_count + 1} to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder to {chat_id}: {e}")


async def check_due_reviews():
    """Check for words due for review and notify users."""
    if not app_reference:
        return
    
    # This would iterate through all users and check for due reviews
    # For simplicity, users can use /review command
    pass


# ============== Main ==============

async def post_init(application: Application):
    """Post initialization - start scheduler."""
    global app_reference
    app_reference = application
    
    # Initialize database
    await db.init_database()
    
    # Add reminder job - runs every minute, checks if 5 min passed
    scheduler.add_job(
        send_reminder_notifications,
        IntervalTrigger(minutes=1),
        id='reminder_job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started - reminders active")


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("words", words_command))
    application.add_handler(CommandHandler("review", review_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("list", list_command))
    
    # Add callback handler for acknowledgments
    application.add_handler(CallbackQueryHandler(acknowledgment_callback))
    
    # Start polling
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
