#!/usr/bin/env python3
"""
Bottel - Telegram Bot for Discounted Udemy Course Enroller
Wraps the DUCE (Discounted Udemy Course Enroller) functionality in a Telegram bot.

Usage:
    Set the TELEGRAM_BOT_TOKEN environment variable and run:
        python bot.py
"""

import asyncio
import json
import os
import queue
import threading
import time
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from base import LoginException, Scraper, Udemy, VERSION, logger, scraper_dict

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Per-user session storage: chat_id -> session dict
user_sessions: dict[int, dict] = {}

os.makedirs("user_data", exist_ok=True)


# ---------------------------------------------------------------------------
# BotUdemy – per-user settings management
# ---------------------------------------------------------------------------

class BotUdemy(Udemy):
    """Udemy subclass with per-user, file-backed settings."""

    def __init__(self, chat_id: int):
        super().__init__("bot")
        self.chat_id = chat_id

    def _settings_file(self) -> str:
        return f"user_data/{self.chat_id}-settings.json"

    def load_settings(self):
        try:
            with open(self._settings_file()) as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            default = os.path.join(os.path.abspath("."), "default-duce-bot-settings.json")
            with open(default) as f:
                self.settings = json.load(f)

        # Migrations (keep in sync with upstream base.py)
        if "course_update_threshold_months" not in self.settings:
            self.settings["course_update_threshold_months"] = 24
        if "Vietnamese" not in self.settings["languages"]:
            self.settings["languages"]["Vietnamese"] = True
        if "Courson" not in self.settings["sites"]:
            self.settings["sites"]["Courson"] = True
        if "Course Joiner" not in self.settings["sites"]:
            self.settings["sites"]["Course Joiner"] = True

        self.settings["languages"] = dict(
            sorted(self.settings["languages"].items(), key=lambda item: item[0])
        )
        self.save_settings()
        # These are overwritten properly by is_user_dumb() before enrollment
        self.title_exclude = "\n".join(self.settings["title_exclude"])
        self.instructor_exclude = "\n".join(self.settings["instructor_exclude"])

    def save_settings(self):
        with open(self._settings_file(), "w") as f:
            json.dump(self.settings, f, indent=4)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def get_session(chat_id: int) -> dict:
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {
            "udemy": None,
            "logged_in": False,
            "running": False,
        }
    return user_sessions[chat_id]


def require_login(session: dict) -> bool:
    return session.get("logged_in") and session.get("udemy") is not None


# ---------------------------------------------------------------------------
# Keyboard builder
# ---------------------------------------------------------------------------

def build_toggle_keyboard(items: dict, prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    row: list[InlineKeyboardButton] = []
    for i, (name, enabled) in enumerate(items.items()):
        emoji = "✅" if enabled else "❌"
        row.append(
            InlineKeyboardButton(
                f"{emoji} {name}", callback_data=f"{prefix}:{name}"
            )
        )
        if len(row) == 2 or i == len(items) - 1:
            buttons.append(row)
            row = []
    buttons.append(
        [InlineKeyboardButton("💾 Done", callback_data=f"{prefix}:done")]
    )
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start and /help."""
    session = get_session(update.effective_chat.id)
    if session["logged_in"]:
        status = f"Logged in as *{session['udemy'].display_name}*"
    else:
        status = "Not logged in"

    text = (
        f"🤖 *Bottel — Udemy Course Enroller Bot*\n"
        f"Version: `{VERSION}`\n\n"
        f"Status: {status}\n\n"
        f"*Commands*\n"
        f"`/login <email> <password>` — Authenticate with Udemy\n"
        f"`/run` — Start scraping & enrolling\n"
        f"`/status` — Show session stats\n"
        f"`/settings` — View current settings\n"
        f"`/setsites` — Toggle scraping sites\n"
        f"`/setlanguages` — Toggle course languages\n"
        f"`/setcategories` — Toggle course categories\n"
        f"`/setminrating <0‑5>` — Minimum course rating\n"
        f"`/excludeinstructor <slug>` — Block an instructor\n"
        f"`/excludekeyword <word>` — Block a title keyword\n"
        f"`/clearexclusions` — Remove all exclusions\n"
        f"`/discountedonly` — Toggle discounted-only mode\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /login <email> <password>."""
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Usage: `/login <email> <password>`", parse_mode="Markdown"
        )
        return

    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    if session["running"]:
        await update.message.reply_text(
            "Enrollment is currently running. Please wait until it finishes."
        )
        return

    email = args[0]
    password = " ".join(args[1:])

    msg = await update.message.reply_text("⏳ Logging in to Udemy…")

    try:
        udemy = BotUdemy(chat_id)
        udemy.load_settings()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, udemy.manual_login, email, password)

        await msg.edit_text("⏳ Fetching session info…")
        await loop.run_in_executor(None, udemy.get_session_info)

        udemy.settings["email"] = email
        udemy.settings["password"] = password
        udemy.save_settings()

        session["udemy"] = udemy
        session["logged_in"] = True

        await msg.edit_text(
            f"✅ Logged in as *{udemy.display_name}*\n"
            f"Currency: `{udemy.currency.upper()}`\n"
            f"Already enrolled courses: `{len(udemy.enrolled_courses)}`",
            parse_mode="Markdown",
        )
    except LoginException as e:
        await msg.edit_text(f"❌ Login failed: {e}")
    except Exception as e:
        logger.exception(f"Login error for chat_id={chat_id}")
        await msg.edit_text(f"❌ Unexpected error: {e}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status."""
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text(
            "Not logged in. Use `/login <email> <password>` first.",
            parse_mode="Markdown",
        )
        return

    udemy: BotUdemy = session["udemy"]
    state = "🔄 Running" if session["running"] else "⏸ Idle"

    text = (
        f"*Session Status*\n"
        f"User: *{udemy.display_name}*\n"
        f"Currency: `{udemy.currency.upper()}`\n"
        f"Enrolled courses: `{len(udemy.enrolled_courses)}`\n"
        f"State: {state}\n\n"
        f"*Last Run Stats*\n"
        f"✅ Successfully enrolled: `{udemy.successfully_enrolled_c}`\n"
        f"💰 Amount saved: `{round(udemy.amount_saved_c, 2)} {udemy.currency.upper()}`\n"
        f"📚 Already enrolled: `{udemy.already_enrolled_c}`\n"
        f"⛔ Excluded: `{udemy.excluded_c}`\n"
        f"❌ Expired: `{udemy.expired_c}`\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings."""
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in. Use /login first.")
        return

    udemy: BotUdemy = session["udemy"]
    s = udemy.settings

    active_sites = [k for k, v in s["sites"].items() if v]
    active_langs = [k for k, v in s["languages"].items() if v]
    active_cats = [k for k, v in s["categories"].items() if v]

    text = (
        f"*Current Settings*\n\n"
        f"*Sites* ({len(active_sites)}/{len(s['sites'])}):\n"
        f"{', '.join(active_sites) or 'None'}\n\n"
        f"*Languages* ({len(active_langs)}/{len(s['languages'])}):\n"
        f"{', '.join(active_langs) or 'None'}\n\n"
        f"*Categories* ({len(active_cats)}/{len(s['categories'])}):\n"
        f"{', '.join(active_cats) or 'None'}\n\n"
        f"*Min Rating:* `{s['min_rating']}`\n"
        f"*Discounted Only:* `{s['discounted_only']}`\n"
        f"*Update Threshold:* `{s['course_update_threshold_months']}` months\n"
        f"*Excluded Instructors:* {', '.join(s['instructor_exclude']) or 'None'}\n"
        f"*Excluded Keywords:* {', '.join(s['title_exclude']) or 'None'}\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_setsites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    udemy: BotUdemy = session["udemy"]
    keyboard = build_toggle_keyboard(udemy.settings["sites"], "sites")
    await update.message.reply_text("Toggle scraping sites:", reply_markup=keyboard)


async def cmd_setlanguages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    udemy: BotUdemy = session["udemy"]
    keyboard = build_toggle_keyboard(udemy.settings["languages"], "languages")
    await update.message.reply_text("Toggle languages:", reply_markup=keyboard)


async def cmd_setcategories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    udemy: BotUdemy = session["udemy"]
    keyboard = build_toggle_keyboard(udemy.settings["categories"], "categories")
    await update.message.reply_text("Toggle categories:", reply_markup=keyboard)


async def cmd_setminrating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: `/setminrating <0-5>`", parse_mode="Markdown"
        )
        return
    try:
        rating = float(args[0])
        if not 0.0 <= rating <= 5.0:
            raise ValueError("Must be between 0 and 5")
        session["udemy"].settings["min_rating"] = rating
        session["udemy"].save_settings()
        await update.message.reply_text(f"Minimum rating set to `{rating}`", parse_mode="Markdown")
    except ValueError as e:
        await update.message.reply_text(f"Invalid value: {e}")


async def cmd_exclude_instructor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: `/excludeinstructor <instructor-slug>`\n"
            "The slug is the URL segment from the instructor's Udemy profile.",
            parse_mode="Markdown",
        )
        return
    name = args[0]
    udemy: BotUdemy = session["udemy"]
    if name not in udemy.settings["instructor_exclude"]:
        udemy.settings["instructor_exclude"].append(name)
        udemy.save_settings()
    await update.message.reply_text(
        f"Instructor `{name}` added to exclusion list.", parse_mode="Markdown"
    )


async def cmd_exclude_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: `/excludekeyword <keyword>`", parse_mode="Markdown"
        )
        return
    keyword = " ".join(args)
    udemy: BotUdemy = session["udemy"]
    if keyword not in udemy.settings["title_exclude"]:
        udemy.settings["title_exclude"].append(keyword)
        udemy.save_settings()
    await update.message.reply_text(
        f"Keyword `{keyword}` added to exclusion list.", parse_mode="Markdown"
    )


async def cmd_clear_exclusions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    udemy: BotUdemy = session["udemy"]
    udemy.settings["instructor_exclude"] = []
    udemy.settings["title_exclude"] = []
    udemy.save_settings()
    await update.message.reply_text("All exclusions cleared.")


async def cmd_discountedonly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_chat.id)
    if not require_login(session):
        await update.message.reply_text("Not logged in.")
        return
    udemy: BotUdemy = session["udemy"]
    current = udemy.settings.get("discounted_only", False)
    udemy.settings["discounted_only"] = not current
    udemy.save_settings()
    state = "enabled" if udemy.settings["discounted_only"] else "disabled"
    await update.message.reply_text(f"Discounted-only mode {state}.")


# ---------------------------------------------------------------------------
# Callback query handler (inline keyboard toggles)
# ---------------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    if not require_login(session):
        return

    udemy: BotUdemy = session["udemy"]
    data: str = query.data

    if ":" not in data:
        return

    prefix, value = data.split(":", 1)

    if value == "done":
        udemy.save_settings()
        try:
            await query.edit_message_text("✅ Settings saved!")
        except BadRequest:
            pass
        return

    if prefix in ("sites", "languages", "categories"):
        if value in udemy.settings[prefix]:
            udemy.settings[prefix][value] = not udemy.settings[prefix][value]
        keyboard = build_toggle_keyboard(udemy.settings[prefix], prefix)
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except BadRequest:
            pass


# ---------------------------------------------------------------------------
# /run — enrollment command
# ---------------------------------------------------------------------------

async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /run — scrape and enroll."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    if not require_login(session):
        await update.message.reply_text(
            "Not logged in. Use `/login <email> <password>` first.",
            parse_mode="Markdown",
        )
        return

    if session["running"]:
        await update.message.reply_text("⚠️ Enrollment is already running!")
        return

    udemy: BotUdemy = session["udemy"]

    if udemy.is_user_dumb():
        await update.message.reply_text(
            "⚠️ No sites, languages, or categories are selected.\n"
            "Use /setsites, /setlanguages, /setcategories to configure."
        )
        return

    session["running"] = True

    # Reset counters for this run
    udemy.successfully_enrolled_c = 0
    udemy.already_enrolled_c = 0
    udemy.expired_c = 0
    udemy.excluded_c = 0
    from decimal import Decimal
    udemy.amount_saved_c = Decimal(0)

    msg = await update.message.reply_text("🚀 Starting enrollment process…")
    prog_queue: queue.Queue = queue.Queue()

    def enrollment_task():
        try:
            scraper = Scraper(udemy.sites)

            def scraping_target(site: str):
                code = scraper_dict[site]
                getattr(scraper, code)()

            prog_queue.put(("status", "Scraping courses from selected sites…"))
            udemy.scraped_data = scraper.get_scraped_courses(scraping_target)
            total = len(udemy.scraped_data)
            prog_queue.put(("status", f"Found {total} courses to process…"))

            last_update_time = [time.time()]

            def update_progress():
                now = time.time()
                if now - last_update_time[0] >= 5:
                    last_update_time[0] = now
                    prog_queue.put(
                        (
                            "progress",
                            {
                                "enrolled": udemy.successfully_enrolled_c,
                                "already": udemy.already_enrolled_c,
                                "expired": udemy.expired_c,
                                "excluded": udemy.excluded_c,
                                "saved": round(udemy.amount_saved_c, 2),
                                "processed": udemy.total_courses_processed,
                                "total": total,
                                "currency": udemy.currency.upper(),
                            },
                        )
                    )

            udemy.update_progress = update_progress
            udemy.start_new_enroll()

            prog_queue.put(
                (
                    "done",
                    {
                        "enrolled": udemy.successfully_enrolled_c,
                        "already": udemy.already_enrolled_c,
                        "expired": udemy.expired_c,
                        "excluded": udemy.excluded_c,
                        "saved": round(udemy.amount_saved_c, 2),
                        "currency": udemy.currency.upper(),
                    },
                )
            )
        except Exception as e:
            logger.exception(f"Enrollment error for chat_id={chat_id}")
            prog_queue.put(("error", str(e)))
        finally:
            session["running"] = False

    thread = threading.Thread(target=enrollment_task, daemon=True)
    thread.start()

    # Monitor the queue and relay progress to Telegram
    while True:
        try:
            msg_type, data = prog_queue.get_nowait()
        except queue.Empty:
            if not session["running"] and prog_queue.empty():
                break
            await asyncio.sleep(1)
            continue

        try:
            if msg_type == "status":
                await msg.edit_text(f"⏳ {data}")

            elif msg_type == "progress":
                text = (
                    f"🔄 *Processing courses…*\n"
                    f"Progress: `{data['processed']}/{data['total']}`\n\n"
                    f"✅ Enrolled: `{data['enrolled']}`\n"
                    f"💰 Saved: `{data['saved']} {data['currency']}`\n"
                    f"📚 Already enrolled: `{data['already']}`\n"
                    f"⛔ Excluded: `{data['excluded']}`\n"
                    f"❌ Expired: `{data['expired']}`\n"
                )
                try:
                    await msg.edit_text(text, parse_mode="Markdown")
                except BadRequest:
                    pass

            elif msg_type == "done":
                text = (
                    f"🎉 *Enrollment Complete!*\n\n"
                    f"✅ Successfully enrolled: *{data['enrolled']}*\n"
                    f"💰 Amount saved: *{data['saved']} {data['currency']}*\n"
                    f"📚 Already enrolled: `{data['already']}`\n"
                    f"⛔ Excluded: `{data['excluded']}`\n"
                    f"❌ Expired: `{data['expired']}`\n"
                )
                await msg.edit_text(text, parse_mode="Markdown")
                break

            elif msg_type == "error":
                await msg.edit_text(f"❌ Error during enrollment:\n`{data}`", parse_mode="Markdown")
                break

        except Exception as e:
            logger.error(f"Error updating Telegram message: {e}")

        await asyncio.sleep(0.1)

    session["running"] = False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not BOT_TOKEN:
        print(
            "ERROR: TELEGRAM_BOT_TOKEN environment variable is not set.\n"
            "Set it and rerun:  export TELEGRAM_BOT_TOKEN=<your-token>"
        )
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("login", cmd_login))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("run", cmd_run))
    app.add_handler(CommandHandler("setsites", cmd_setsites))
    app.add_handler(CommandHandler("setlanguages", cmd_setlanguages))
    app.add_handler(CommandHandler("setcategories", cmd_setcategories))
    app.add_handler(CommandHandler("setminrating", cmd_setminrating))
    app.add_handler(CommandHandler("excludeinstructor", cmd_exclude_instructor))
    app.add_handler(CommandHandler("excludekeyword", cmd_exclude_keyword))
    app.add_handler(CommandHandler("clearexclusions", cmd_clear_exclusions))
    app.add_handler(CommandHandler("discountedonly", cmd_discountedonly))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print(f"Bottel {VERSION} is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
