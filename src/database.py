"""
Database module for storing vocabulary, learning progress, and notifications.
Uses SQLite with async support for non-blocking operations.
"""

import aiosqlite
import os
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bottel.db")


class ReviewStage(Enum):
    """Spaced repetition stages based on Ebbinghaus forgetting curve"""
    NEW = 0           # Just learned
    STAGE_1 = 1       # Review after 24 hours
    STAGE_2 = 2       # Review after 2-3 days
    STAGE_3 = 3       # Review after 1 week
    STAGE_4 = 4       # Review after 2 weeks
    STAGE_5 = 5       # Review after 1 month
    MASTERED = 6      # Fully learned


# Intervals for each stage (in hours)
REVIEW_INTERVALS = {
    ReviewStage.NEW: 24,        # 24 hours for first review
    ReviewStage.STAGE_1: 60,    # ~2.5 days
    ReviewStage.STAGE_2: 168,   # 1 week
    ReviewStage.STAGE_3: 336,   # 2 weeks
    ReviewStage.STAGE_4: 720,   # ~1 month
    ReviewStage.STAGE_5: 2160,  # ~3 months (final reinforcement)
}


@dataclass
class Word:
    id: int
    word: str
    context: Optional[str]  # Original tweet/context
    definition: Optional[str]
    example: Optional[str]
    source_tweet_id: Optional[str]
    created_at: datetime
    review_stage: ReviewStage
    next_review_at: datetime
    times_reviewed: int
    is_read: bool


@dataclass
class PendingNotification:
    id: int
    word_id: int
    message_id: Optional[int]
    created_at: datetime
    is_read: bool
    last_reminder_at: Optional[datetime]
    reminder_count: int


async def init_database():
    """Initialize the database with required tables."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Words table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                context TEXT,
                definition TEXT,
                example TEXT,
                source_tweet_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                review_stage INTEGER DEFAULT 0,
                next_review_at TIMESTAMP,
                times_reviewed INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(word)
            )
        """)
        
        # Pending notifications table - tracks unread messages
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER,
                message_id INTEGER,
                batch_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                last_reminder_at TIMESTAMP,
                reminder_count INTEGER DEFAULT 0,
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        """)
        
        # Daily batches - track what was sent each day
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT UNIQUE,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER,
                new_word_count INTEGER,
                review_word_count INTEGER,
                is_read BOOLEAN DEFAULT 0,
                message_id INTEGER
            )
        """)
        
        # Processed tweets - avoid duplicates
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processed_tweets (
                tweet_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User settings
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        await db.commit()
        print("✅ Database initialized successfully")


async def add_word(word: str, context: Optional[str] = None, 
                   definition: Optional[str] = None, example: Optional[str] = None,
                   source_tweet_id: Optional[str] = None) -> Optional[int]:
    """Add a new word to the database. Returns word ID or None if duplicate."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            # Set first review to 24 hours from now
            next_review = datetime.now() + timedelta(hours=24)
            cursor = await db.execute("""
                INSERT INTO words (word, context, definition, example, source_tweet_id, next_review_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (word.lower().strip(), context, definition, example, source_tweet_id, next_review))
            await db.commit()
            return cursor.lastrowid
        except aiosqlite.IntegrityError:
            # Word already exists
            return None


async def get_words_for_review(limit: int = 15) -> List[Word]:
    """Get words that are due for review based on spaced repetition schedule."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM words 
            WHERE is_active = 1 
              AND next_review_at <= ?
              AND review_stage < ?
            ORDER BY next_review_at ASC
            LIMIT ?
        """, (datetime.now(), ReviewStage.MASTERED.value, limit))
        rows = await cursor.fetchall()
        
        return [Word(
            id=row['id'],
            word=row['word'],
            context=row['context'],
            definition=row['definition'],
            example=row['example'],
            source_tweet_id=row['source_tweet_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            review_stage=ReviewStage(row['review_stage']),
            next_review_at=datetime.fromisoformat(row['next_review_at']) if row['next_review_at'] else datetime.now(),
            times_reviewed=row['times_reviewed'],
            is_read=False
        ) for row in rows]


async def get_new_words(limit: int = 15) -> List[Word]:
    """Get newly added words that haven't been sent yet (stage NEW, never reviewed)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM words 
            WHERE is_active = 1 
              AND review_stage = 0
              AND times_reviewed = 0
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        
        return [Word(
            id=row['id'],
            word=row['word'],
            context=row['context'],
            definition=row['definition'],
            example=row['example'],
            source_tweet_id=row['source_tweet_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            review_stage=ReviewStage(row['review_stage']),
            next_review_at=datetime.fromisoformat(row['next_review_at']) if row['next_review_at'] else datetime.now(),
            times_reviewed=row['times_reviewed'],
            is_read=False
        ) for row in rows]


async def mark_word_reviewed(word_id: int):
    """Mark a word as reviewed and schedule next review based on memory curve."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get current stage
        cursor = await db.execute(
            "SELECT review_stage, times_reviewed FROM words WHERE id = ?", (word_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return
        
        current_stage = ReviewStage(row[0])
        times_reviewed = row[1]
        
        # Move to next stage
        if current_stage.value < ReviewStage.MASTERED.value:
            next_stage = ReviewStage(current_stage.value + 1)
        else:
            next_stage = ReviewStage.MASTERED
        
        # Calculate next review time
        if next_stage in REVIEW_INTERVALS:
            next_review = datetime.now() + timedelta(hours=REVIEW_INTERVALS[next_stage])
        else:
            # Mastered - set far future date
            next_review = datetime.now() + timedelta(days=365)
        
        await db.execute("""
            UPDATE words 
            SET review_stage = ?, next_review_at = ?, times_reviewed = ?
            WHERE id = ?
        """, (next_stage.value, next_review, times_reviewed + 1, word_id))
        await db.commit()


async def create_notification(word_id: int, message_id: int, batch_id: str) -> int:
    """Create a pending notification for tracking read status."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO pending_notifications (word_id, message_id, batch_id, last_reminder_at)
            VALUES (?, ?, ?, ?)
        """, (word_id, message_id, batch_id, datetime.now()))
        await db.commit()
        return cursor.lastrowid


async def create_batch(batch_id: str, word_count: int, new_count: int, 
                       review_count: int, message_id: int):
    """Record a daily batch of words sent."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO daily_batches (batch_id, word_count, new_word_count, review_word_count, message_id)
            VALUES (?, ?, ?, ?, ?)
        """, (batch_id, word_count, new_count, review_count, message_id))
        await db.commit()


async def mark_batch_read(batch_id: str):
    """Mark a batch as read."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE daily_batches SET is_read = 1 WHERE batch_id = ?", (batch_id,)
        )
        await db.execute(
            "UPDATE pending_notifications SET is_read = 1 WHERE batch_id = ?", (batch_id,)
        )
        await db.commit()


async def get_unread_batches() -> List[Tuple[str, int, datetime, int]]:
    """Get all unread batches with their message IDs for reminder notifications."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT batch_id, message_id, sent_at, 
                   (SELECT COUNT(*) FROM pending_notifications WHERE batch_id = daily_batches.batch_id) as reminder_count
            FROM daily_batches 
            WHERE is_read = 0
            ORDER BY sent_at ASC
        """)
        rows = await cursor.fetchall()
        return [(row['batch_id'], row['message_id'], 
                 datetime.fromisoformat(row['sent_at']), row['reminder_count']) for row in rows]


async def update_reminder_sent(batch_id: str):
    """Update the reminder count for a batch."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE pending_notifications 
            SET reminder_count = reminder_count + 1, last_reminder_at = ?
            WHERE batch_id = ?
        """, (datetime.now(), batch_id))
        await db.commit()


async def is_tweet_processed(tweet_id: str) -> bool:
    """Check if a tweet has already been processed."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM processed_tweets WHERE tweet_id = ?", (tweet_id,)
        )
        return await cursor.fetchone() is not None


async def mark_tweet_processed(tweet_id: str):
    """Mark a tweet as processed."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO processed_tweets (tweet_id) VALUES (?)", (tweet_id,)
        )
        await db.commit()


async def get_setting(key: str) -> Optional[str]:
    """Get a setting value."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_setting(key: str, value: str):
    """Set a setting value."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        await db.commit()


async def get_all_words_count() -> int:
    """Get total count of words in database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM words WHERE is_active = 1")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_words_by_stage() -> dict:
    """Get count of words at each review stage."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT review_stage, COUNT(*) 
            FROM words 
            WHERE is_active = 1 
            GROUP BY review_stage
        """)
        rows = await cursor.fetchall()
        return {ReviewStage(row[0]).name: row[1] for row in rows}
