"""
Database module for vocabulary spaced repetition bot.
Uses SQLite with async support.
"""

import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import json

DATABASE_PATH = "vocab_bot.db"

# Spaced repetition intervals (Ebbinghaus forgetting curve)
# Intervals in hours: 24h, 72h (3 days), 168h (7 days), 336h (14 days), 720h (30 days), 2160h (90 days)
REVIEW_INTERVALS = [24, 72, 168, 336, 720, 2160]


async def init_database():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Words table - stores all vocabulary
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                definition TEXT,
                example TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(word)
            )
        """)
        
        # User table - stores user info and chat_id
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Review schedule table - tracks when words need to be reviewed
        await db.execute("""
            CREATE TABLE IF NOT EXISTS review_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                review_level INTEGER DEFAULT 0,
                next_review TIMESTAMP NOT NULL,
                last_reviewed TIMESTAMP,
                acknowledged INTEGER DEFAULT 0,
                sent_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (word_id) REFERENCES words(id),
                UNIQUE(user_id, word_id)
            )
        """)
        
        # Daily batches - tracks which words were sent together as daily batch
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                batch_date DATE NOT NULL,
                word_ids TEXT NOT NULL,
                sent_at TIMESTAMP,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Pending notifications - tracks unread messages needing reminders
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                batch_id INTEGER,
                message_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_reminder TIMESTAMP,
                reminder_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (batch_id) REFERENCES daily_batches(id)
            )
        """)
        
        await db.commit()


async def add_user(chat_id: int, username: str = None) -> int:
    """Add a new user or get existing user id."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        
        cursor = await db.execute(
            "INSERT INTO users (chat_id, username) VALUES (?, ?)",
            (chat_id, username)
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_by_chat_id(chat_id: int) -> Optional[Tuple]:
    """Get user by chat_id."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, chat_id, username FROM users WHERE chat_id = ?",
            (chat_id,)
        )
        return await cursor.fetchone()


async def add_word(word: str, definition: str = None, example: str = None, source: str = None) -> int:
    """Add a new word to the database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.execute(
                "INSERT INTO words (word, definition, example, source) VALUES (?, ?, ?, ?)",
                (word, definition, example, source)
            )
            await db.commit()
            return cursor.lastrowid
        except aiosqlite.IntegrityError:
            # Word already exists, return existing id
            cursor = await db.execute(
                "SELECT id FROM words WHERE word = ?", (word,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None


async def add_words_bulk(words: List[dict]) -> List[int]:
    """Add multiple words at once."""
    word_ids = []
    for word_data in words:
        word_id = await add_word(
            word=word_data.get('word'),
            definition=word_data.get('definition'),
            example=word_data.get('example'),
            source=word_data.get('source')
        )
        if word_id:
            word_ids.append(word_id)
    return word_ids


async def get_unscheduled_words(user_id: int, limit: int = 15) -> List[Tuple]:
    """Get words that haven't been scheduled for a user yet."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT w.id, w.word, w.definition, w.example, w.source
            FROM words w
            WHERE w.id NOT IN (
                SELECT word_id FROM review_schedule WHERE user_id = ?
            )
            ORDER BY w.created_at ASC
            LIMIT ?
        """, (user_id, limit))
        return await cursor.fetchall()


async def schedule_words_for_user(user_id: int, word_ids: List[int], review_time: datetime = None):
    """Schedule words for initial review."""
    if review_time is None:
        review_time = datetime.now()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for word_id in word_ids:
            try:
                await db.execute("""
                    INSERT INTO review_schedule (user_id, word_id, review_level, next_review)
                    VALUES (?, ?, 0, ?)
                """, (user_id, word_id, review_time))
            except aiosqlite.IntegrityError:
                pass  # Already scheduled
        await db.commit()


async def get_words_due_for_review(user_id: int) -> List[Tuple]:
    """Get words that are due for review (spaced repetition)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT rs.id, rs.word_id, rs.review_level, w.word, w.definition, w.example
            FROM review_schedule rs
            JOIN words w ON rs.word_id = w.id
            WHERE rs.user_id = ? 
            AND rs.next_review <= datetime('now')
            AND rs.acknowledged = 0
            ORDER BY rs.review_level ASC, rs.next_review ASC
        """, (user_id,))
        return await cursor.fetchall()


async def mark_review_sent(schedule_ids: List[int]):
    """Mark reviews as sent."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for sid in schedule_ids:
            await db.execute("""
                UPDATE review_schedule 
                SET sent_at = datetime('now')
                WHERE id = ?
            """, (sid,))
        await db.commit()


async def acknowledge_review(schedule_id: int):
    """Mark a review as acknowledged and schedule next review."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get current review level
        cursor = await db.execute(
            "SELECT review_level FROM review_schedule WHERE id = ?",
            (schedule_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return
        
        current_level = row[0]
        next_level = min(current_level + 1, len(REVIEW_INTERVALS) - 1)
        hours_until_next = REVIEW_INTERVALS[next_level]
        next_review = datetime.now() + timedelta(hours=hours_until_next)
        
        await db.execute("""
            UPDATE review_schedule 
            SET acknowledged = 1,
                last_reviewed = datetime('now'),
                review_level = ?,
                next_review = ?
            WHERE id = ?
        """, (next_level, next_review, schedule_id))
        await db.commit()


async def reset_acknowledgment_for_next_cycle(schedule_id: int):
    """Reset acknowledgment flag for next review cycle."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE review_schedule 
            SET acknowledged = 0, sent_at = NULL
            WHERE id = ?
        """, (schedule_id,))
        await db.commit()


async def create_daily_batch(user_id: int, word_ids: List[int]) -> int:
    """Create a daily batch of words."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        today = datetime.now().date()
        cursor = await db.execute("""
            INSERT INTO daily_batches (user_id, batch_date, word_ids, sent_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (user_id, today, json.dumps(word_ids)))
        await db.commit()
        return cursor.lastrowid


async def get_unacknowledged_batch(user_id: int) -> Optional[Tuple]:
    """Get the latest unacknowledged batch for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT id, batch_date, word_ids, sent_at
            FROM daily_batches
            WHERE user_id = ? AND acknowledged = 0
            ORDER BY sent_at DESC
            LIMIT 1
        """, (user_id,))
        return await cursor.fetchone()


async def acknowledge_batch(batch_id: int):
    """Mark a batch as acknowledged."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE daily_batches 
            SET acknowledged = 1, acknowledged_at = datetime('now')
            WHERE id = ?
        """, (batch_id,))
        await db.commit()


async def add_pending_notification(user_id: int, batch_id: int, message_type: str) -> int:
    """Add a pending notification."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO pending_notifications (user_id, batch_id, message_type)
            VALUES (?, ?, ?)
        """, (user_id, batch_id, message_type))
        await db.commit()
        return cursor.lastrowid


async def get_pending_notifications() -> List[Tuple]:
    """Get all pending notifications that need reminders."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT pn.id, pn.user_id, pn.batch_id, pn.message_type, pn.last_reminder, pn.reminder_count, u.chat_id
            FROM pending_notifications pn
            JOIN users u ON pn.user_id = u.id
            JOIN daily_batches db ON pn.batch_id = db.id
            WHERE db.acknowledged = 0
        """)
        return await cursor.fetchall()


async def update_notification_reminder(notification_id: int):
    """Update last reminder time for a notification."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE pending_notifications 
            SET last_reminder = datetime('now'), reminder_count = reminder_count + 1
            WHERE id = ?
        """, (notification_id,))
        await db.commit()


async def remove_pending_notification(batch_id: int):
    """Remove pending notification when batch is acknowledged."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM pending_notifications WHERE batch_id = ?",
            (batch_id,)
        )
        await db.commit()


async def get_all_words() -> List[Tuple]:
    """Get all words in the database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, word, definition, example, source FROM words ORDER BY created_at DESC"
        )
        return await cursor.fetchall()


async def get_word_count() -> int:
    """Get total word count."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM words")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_user_stats(user_id: int) -> dict:
    """Get learning statistics for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Total words learned
        cursor = await db.execute(
            "SELECT COUNT(*) FROM review_schedule WHERE user_id = ?",
            (user_id,)
        )
        total_learned = (await cursor.fetchone())[0]
        
        # Words mastered (at highest review level)
        cursor = await db.execute(
            "SELECT COUNT(*) FROM review_schedule WHERE user_id = ? AND review_level >= ?",
            (user_id, len(REVIEW_INTERVALS) - 1)
        )
        mastered = (await cursor.fetchone())[0]
        
        # Words due for review
        cursor = await db.execute("""
            SELECT COUNT(*) FROM review_schedule 
            WHERE user_id = ? AND next_review <= datetime('now') AND acknowledged = 0
        """, (user_id,))
        due_for_review = (await cursor.fetchone())[0]
        
        return {
            'total_learned': total_learned,
            'mastered': mastered,
            'due_for_review': due_for_review
        }
