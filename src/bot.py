"""
Telegram Bot for vocabulary learning with spaced repetition.
Features:
- Daily vocabulary from Twitter feed
- Read confirmation tracking
- 5-minute reminder notifications until read
- Memory curve (spaced repetition) scheduling
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
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from database import (
    init_database, 
    add_word, 
    get_words_for_review, 
    get_new_words,
    mark_word_reviewed,
    create_batch,
    mark_batch_read,
    get_unread_batches,
    update_reminder_sent,
    get_setting,
    set_setting,
    get_all_words_count,
    get_words_by_stage,
    ReviewStage
)
from twitter_scraper import fetch_and_extract_vocabulary, ExtractedWord

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Global scheduler
scheduler: Optional[AsyncIOScheduler] = None
app: Optional[Application] = None


def format_word_message(word_data: dict, index: int, total: int, is_review: bool = False) -> str:
    """Format a single word for display."""
    review_badge = "🔄 REVIEW" if is_review else "✨ NEW"
    stage_info = f" (Stage {word_data.get('stage', 0)})" if is_review else ""
    
    return f"""
{review_badge}{stage_info} [{index}/{total}]

📚 **{word_data['word']}**
_{word_data.get('difficulty', 'C1-C2')}_

📖 **Definition:**
{word_data['definition']}

💬 **Example:**
_{word_data['example']}_

📌 **Context:**
>{word_data.get('context', 'From your Twitter feed')[:200]}...
"""


def create_vocabulary_message(new_words: list, review_words: list, batch_id: str) -> tuple[str, InlineKeyboardMarkup]:
    """Create the full vocabulary message with all words."""
    
    lines = ["🎯 **YOUR DAILY VOCABULARY**\n"]
    lines.append(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    lines.append(f"📊 {len(new_words)} new + {len(review_words)} review = {len(new_words) + len(review_words)} words\n")
    lines.append("─" * 30)
    
    # New words section
    if new_words:
        lines.append("\n✨ **NEW WORDS**\n")
        for i, word in enumerate(new_words, 1):
            lines.append(f"""
**{i}. {word['word']}** _({word.get('difficulty', 'C1')})_
   📖 {word['definition']}
   💬 _{word['example']}_
""")
    
    # Review words section
    if review_words:
        lines.append("\n🔄 **REVIEW WORDS** (Memory Curve)\n")
        for i, word in enumerate(review_words, 1):
            stage = word.get('stage', 1)
            stage_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"][min(stage-1, 5)]
            lines.append(f"""
**{i}. {word['word']}** {stage_emoji}
   📖 {word['definition']}
   💬 _{word['example']}_
""")
    
    lines.append("\n─" * 30)
    lines.append("\n⬇️ **Tap the button below when you've read all words**")
    
    # Create "I've read it" button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I've read all words", callback_data=f"read_{batch_id}")]
    ])
    
    return "\n".join(lines), keyboard


async def send_vocabulary_batch(context: ContextTypes.DEFAULT_TYPE, chat_id: int = None):
    """Send daily vocabulary batch to user."""
    if not chat_id:
        chat_id = CHAT_ID or await get_setting("chat_id")
    
    if not chat_id:
        print("❌ No chat ID configured!")
        return
    
    chat_id = int(chat_id)
    print(f"📤 Sending vocabulary batch to chat {chat_id}...")
    
    # Fetch new vocabulary from Twitter
    print("🐦 Fetching from Twitter feed...")
    extracted_words = await fetch_and_extract_vocabulary(word_count=15)
    
    # Store new words in database
    new_words = []
    for ew in extracted_words:
        word_id = await add_word(
            word=ew.word,
            context=ew.context,
            definition=ew.definition,
            example=ew.example
        )
        if word_id:
            new_words.append({
                "id": word_id,
                "word": ew.word,
                "definition": ew.definition,
                "example": ew.example,
                "context": ew.context,
                "difficulty": ew.difficulty
            })
    
    # Get words due for review (memory curve)
    review_word_objects = await get_words_for_review(limit=10)
    review_words = [{
        "id": w.id,
        "word": w.word,
        "definition": w.definition or "Definition not available",
        "example": w.example or "Example not available",
        "context": w.context or "",
        "stage": w.review_stage.value
    } for w in review_word_objects]
    
    if not new_words and not review_words:
        await context.bot.send_message(
            chat_id=chat_id,
            text="📭 No new vocabulary today. Check back tomorrow!",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Generate unique batch ID
    batch_id = str(uuid.uuid4())[:8]
    
    # Create and send message
    message_text, keyboard = create_vocabulary_message(new_words, review_words, batch_id)
    
    try:
        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Store batch in database
        await create_batch(
            batch_id=batch_id,
            word_count=len(new_words) + len(review_words),
            new_count=len(new_words),
            review_count=len(review_words),
            message_id=sent_message.message_id
        )
        
        print(f"✅ Sent batch {batch_id} with {len(new_words)} new + {len(review_words)} review words")
        
        # Schedule reminder check
        if scheduler:
            scheduler.add_job(
                check_and_remind,
                trigger=IntervalTrigger(minutes=5),
                args=[context, chat_id, batch_id],
                id=f"reminder_{batch_id}",
                replace_existing=True,
                max_instances=1
            )
            
    except Exception as e:
        print(f"❌ Failed to send message: {e}")


async def check_and_remind(context: ContextTypes.DEFAULT_TYPE, chat_id: int, batch_id: str):
    """Check if batch is read, send reminder if not."""
    unread = await get_unread_batches()
    
    for b_id, msg_id, sent_at, reminder_count in unread:
        if b_id == batch_id:
            # Still unread - send reminder
            time_elapsed = datetime.now() - sent_at
            minutes = int(time_elapsed.total_seconds() / 60)
            
            reminder_text = f"""
⚠️ **REMINDER** ⚠️

You haven't read your vocabulary yet!
📚 Batch sent {minutes} minutes ago

👆 Please scroll up and read your words, then tap "✅ I've read all words"

_This reminder will repeat every 5 minutes until you confirm._
"""
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=reminder_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=msg_id
                )
                await update_reminder_sent(batch_id)
                print(f"🔔 Sent reminder #{reminder_count + 1} for batch {batch_id}")
            except Exception as e:
                print(f"❌ Failed to send reminder: {e}")
            
            return
    
    # Batch was read - remove the reminder job
    if scheduler:
        try:
            scheduler.remove_job(f"reminder_{batch_id}")
            print(f"✅ Removed reminder job for batch {batch_id}")
        except:
            pass


async def handle_read_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user confirms they've read the words."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("read_"):
        batch_id = data[5:]
        
        # Mark batch as read
        await mark_batch_read(batch_id)
        
        # Mark all words in this batch as reviewed for memory curve
        review_words = await get_words_for_review(limit=50)
        for word in review_words:
            await mark_word_reviewed(word.id)
        
        # Remove reminder job
        if scheduler:
            try:
                scheduler.remove_job(f"reminder_{batch_id}")
            except:
                pass
        
        # Update message
        await query.edit_message_reply_markup(reply_markup=None)
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="""
✅ **Great job!** 

Your words have been marked as read.

📈 **Memory Curve Schedule:**
- These words will come back for review:
  • Tomorrow (24h) - Stage 1
  • In 2-3 days - Stage 2  
  • In 1 week - Stage 3
  • In 2 weeks - Stage 4
  • In 1 month - Stage 5

Keep learning! 🚀
""",
            parse_mode=ParseMode.MARKDOWN
        )
        
        print(f"✅ User confirmed reading batch {batch_id}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = update.effective_chat.id
    await set_setting("chat_id", str(chat_id))
    
    await update.message.reply_text(f"""
🎓 **Welcome to Bottel - Your Vocabulary Bot!**

I'll help you learn advanced English vocabulary (C1-C2 level) from Twitter feeds using spaced repetition.

**How it works:**
1. 📚 I send you 15 new words daily from Twitter
2. ✅ You confirm when you've read them
3. 🔔 If you don't read, I remind you every 5 minutes
4. 🔄 Words come back for review based on memory curve:
   - 24 hours → 2-3 days → 1 week → 2 weeks → 1 month

**Commands:**
/start - Show this message
/vocab - Get vocabulary now
/stats - Show your learning statistics
/settings - Configure your preferences

Your chat ID: `{chat_id}` (saved automatically)

Ready to learn? Use /vocab to get your first batch!
""", parse_mode=ParseMode.MARKDOWN)


async def cmd_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /vocab command - send vocabulary immediately."""
    chat_id = update.effective_chat.id
    await update.message.reply_text("🔄 Fetching vocabulary from Twitter... This may take a moment.")
    await send_vocabulary_batch(context, chat_id)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    total_words = await get_all_words_count()
    stages = await get_words_by_stage()
    
    stats_text = f"""
📊 **Your Learning Statistics**

📚 **Total words learned:** {total_words}

📈 **By Stage:**
"""
    
    stage_names = {
        "NEW": "🆕 New (not reviewed)",
        "STAGE_1": "1️⃣ Stage 1 (24h review)",
        "STAGE_2": "2️⃣ Stage 2 (2-3 days)",
        "STAGE_3": "3️⃣ Stage 3 (1 week)",
        "STAGE_4": "4️⃣ Stage 4 (2 weeks)", 
        "STAGE_5": "5️⃣ Stage 5 (1 month)",
        "MASTERED": "🏆 Mastered"
    }
    
    for stage, name in stage_names.items():
        count = stages.get(stage, 0)
        stats_text += f"\n{name}: {count}"
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command."""
    chat_id = update.effective_chat.id
    
    settings_text = f"""
⚙️ **Settings**

📍 **Your Chat ID:** `{chat_id}`

🐦 **Twitter Accounts:** 
Default list includes: TheEconomist, guardian, NYTimes, TheAtlantic, NewYorker, NPR, BBC, FT

To customize, edit the `.env` file or send me a list of Twitter accounts:
`/accounts @user1 @user2 @user3`

⏰ **Notifications:**
- Vocabulary sent: On demand (/vocab)
- Reminders: Every 5 minutes until read
""" 
    
    await update.message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)


async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command for debugging."""
    await update.message.reply_text(
        f"✅ Bot is working!\nChat ID: {update.effective_chat.id}"
    )


def setup_scheduler(application: Application):
    """Setup APScheduler for periodic tasks."""
    global scheduler
    scheduler = AsyncIOScheduler()
    
    # Check for unread batches every 5 minutes
    async def check_all_unread():
        unread = await get_unread_batches()
        for batch_id, msg_id, sent_at, count in unread:
            # Only remind if batch is older than 5 minutes
            if datetime.now() - sent_at > timedelta(minutes=5):
                await check_and_remind(
                    application, 
                    int(await get_setting("chat_id") or 0),
                    batch_id
                )
    
    scheduler.start()
    print("✅ Scheduler started")


async def post_init(application: Application):
    """Post-initialization hook."""
    await init_database()
    setup_scheduler(application)
    print("✅ Bot initialized")


def main():
    """Main entry point."""
    global app
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    print("🚀 Starting Bottel...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("vocab", cmd_vocab))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CallbackQueryHandler(handle_read_confirmation, pattern="^read_"))
    
    print("✅ Handlers registered")
    print("🤖 Bot is running! Press Ctrl+C to stop.")
    
    # Run the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
