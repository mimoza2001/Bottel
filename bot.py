"""
Bottel – Kali Linux Cybersecurity Telegram Bot
Runs security tools inside the Kali Docker container and reports results.

IMPORTANT: Only use against systems you own or have explicit written permission
to test. Unauthorized scanning / exploitation is illegal.
"""

import asyncio
import base64
import logging
import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from computer_use import run_computer_use_agent, take_screenshot

# ── Configuration ──────────────────────────────────────────────────────────────
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USERS: set[int] = set(
    int(uid)
    for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
)
RESULTS_DIR = Path("/app/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
MAX_MSG_LEN = 4000          # Telegram message character limit (safe margin)
SCAN_TIMEOUT = 120          # seconds before a tool call is killed

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


# ── Auth guard ─────────────────────────────────────────────────────────────────
def authorized(update: Update) -> bool:
    if not ALLOWED_USERS:
        return True                         # open mode – configure ALLOWED_USER_IDS!
    return update.effective_user.id in ALLOWED_USERS


async def deny(update: Update) -> None:
    await update.message.reply_text("Access denied.")


# ── Tool runner ────────────────────────────────────────────────────────────────
async def run_tool(cmd: list[str], timeout: int = SCAN_TIMEOUT) -> str:
    """Run a shell tool asynchronously and return its combined output."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return f"[!] Timed out after {timeout}s"
    except FileNotFoundError:
        return f"[!] Tool not found: {cmd[0]}"
    except Exception as exc:
        return f"[!] Error: {exc}"


def save_result(name: str, content: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{name}_{ts}.txt"
    path.write_text(content)
    return path


def chunk(text: str, size: int = MAX_MSG_LEN):
    """Yield successive chunks of `text` no longer than `size`."""
    for i in range(0, len(text), size):
        yield text[i : i + size]


async def reply_long(update: Update, text: str) -> None:
    for part in chunk(text):
        await update.message.reply_text(f"```\n{part}\n```", parse_mode="Markdown")


# ── Command handlers ───────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    await update.message.reply_text(
        "*Bottel – Kali Cybersecurity Bot*\n\n"
        "*Security tools:*\n"
        "/nmap `<target>` – Port scan\n"
        "/ping `<host>` – Ping host\n"
        "/whois `<domain>` – WHOIS lookup\n"
        "/dns `<domain>` – DNS enumeration\n"
        "/nikto `<url>` – Web vulnerability scan\n"
        "/sqlmap `<url>` – SQL injection test\n"
        "/gobuster `<url>` – Directory brute-force\n"
        "/hash `<type> <hash>` – Crack hash with John\n\n"
        "*Desktop control (Claude Opus 4.6):*\n"
        "/screenshot – Live Kali desktop screenshot\n"
        "/computeruse `<task>` – Let Claude control the desktop\n\n"
        "/help – Show this message",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, ctx)


async def ping_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text("Usage: /ping <host>")
    host = shlex.quote(ctx.args[0])
    await update.message.reply_text(f"Pinging {host}…")
    result = await run_tool(["ping", "-c", "4", host])
    await reply_long(update, result)


async def whois_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text("Usage: /whois <domain>")
    target = shlex.quote(ctx.args[0])
    await update.message.reply_text(f"WHOIS lookup for {target}…")
    result = await run_tool(["whois", target])
    await reply_long(update, result)


async def dns_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text("Usage: /dns <domain>")
    domain = shlex.quote(ctx.args[0])
    await update.message.reply_text(f"DNS enumeration for {domain}…")
    result = await run_tool(["nslookup", domain])
    result += "\n\n" + await run_tool(["dig", "ANY", domain, "+noall", "+answer"])
    await reply_long(update, result)


async def nmap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text("Usage: /nmap <target> [extra flags]")
    # Build a safe nmap command; user may add extra flags but not pipes/subshells
    target = ctx.args[0]
    extra = ctx.args[1:] if len(ctx.args) > 1 else []
    # Reject shell metacharacters
    for token in [target] + extra:
        if any(c in token for c in (";", "&", "|", "`", "$", "(", ")")):
            return await update.message.reply_text("[!] Invalid characters in arguments.")
    cmd = ["nmap", "-sV", "--open", target] + extra
    await update.message.reply_text(f"Running nmap on `{target}`… (may take a while)", parse_mode="Markdown")
    result = await run_tool(cmd, timeout=180)
    path = save_result("nmap", result)
    await reply_long(update, result)
    await update.message.reply_text(f"Results saved to `{path.name}`", parse_mode="Markdown")


async def nikto_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text("Usage: /nikto <url>")
    url = ctx.args[0]
    if any(c in url for c in (";", "&", "|", "`", "$")):
        return await update.message.reply_text("[!] Invalid URL characters.")
    await update.message.reply_text(f"Running Nikto on `{url}`…", parse_mode="Markdown")
    result = await run_tool(["nikto", "-h", url, "-nointeractive"], timeout=180)
    path = save_result("nikto", result)
    await reply_long(update, result)
    await update.message.reply_text(f"Results saved to `{path.name}`", parse_mode="Markdown")


async def sqlmap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text("Usage: /sqlmap <url>")
    url = ctx.args[0]
    if any(c in url for c in (";", "&", "|", "`", "$")):
        return await update.message.reply_text("[!] Invalid URL characters.")
    await update.message.reply_text(f"Running sqlmap on `{url}`…", parse_mode="Markdown")
    result = await run_tool(
        ["sqlmap", "-u", url, "--batch", "--level=1", "--risk=1"],
        timeout=180,
    )
    path = save_result("sqlmap", result)
    await reply_long(update, result)
    await update.message.reply_text(f"Results saved to `{path.name}`", parse_mode="Markdown")


async def gobuster_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text("Usage: /gobuster <url>")
    url = ctx.args[0]
    if any(c in url for c in (";", "&", "|", "`", "$")):
        return await update.message.reply_text("[!] Invalid URL characters.")
    wordlist = "/app/wordlists/common.txt"
    if not Path(wordlist).exists():
        wordlist = "/usr/share/wordlists/dirb/common.txt"
    await update.message.reply_text(f"Running Gobuster on `{url}`…", parse_mode="Markdown")
    result = await run_tool(
        ["gobuster", "dir", "-u", url, "-w", wordlist, "-q"],
        timeout=180,
    )
    path = save_result("gobuster", result)
    await reply_long(update, result)
    await update.message.reply_text(f"Results saved to `{path.name}`", parse_mode="Markdown")


async def hash_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await deny(update)
    if not ctx.args or len(ctx.args) < 2:
        return await update.message.reply_text("Usage: /hash <type> <hash>\nTypes: md5, sha1, sha256")
    hash_type, hash_val = ctx.args[0], ctx.args[1]
    # Validate inputs
    if any(c in hash_type + hash_val for c in (";", "&", "|", "`", "$", "/", "\\")):
        return await update.message.reply_text("[!] Invalid characters.")
    hash_file = RESULTS_DIR / "target.hash"
    hash_file.write_text(hash_val)
    wordlist = "/usr/share/wordlists/rockyou.txt"
    if not Path(wordlist).exists():
        return await update.message.reply_text("[!] rockyou.txt wordlist not found.")
    await update.message.reply_text(f"Cracking `{hash_type}` hash with John…", parse_mode="Markdown")
    result = await run_tool(
        ["john", f"--format={hash_type}", f"--wordlist={wordlist}", str(hash_file)],
        timeout=120,
    )
    result += "\n\n" + await run_tool(["john", "--show", str(hash_file)])
    await reply_long(update, result)


async def screenshot_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a live screenshot of the Kali desktop to the user."""
    if not authorized(update):
        return await deny(update)
    await update.message.reply_text("Taking screenshot of Kali desktop…")
    try:
        img_b64 = await take_screenshot()
        img_bytes = base64.b64decode(img_b64)
        await update.message.reply_photo(photo=img_bytes, caption="Kali desktop screenshot")
    except Exception as exc:
        await update.message.reply_text(f"[!] Screenshot failed: {exc}")


async def computeruse_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /computeruse <task>
    Let Claude control the Kali desktop autonomously to complete a task.
    Claude Opus 4.6 with computer_20251124 tool — sees and clicks the screen.
    """
    if not authorized(update):
        return await deny(update)
    if not ctx.args:
        return await update.message.reply_text(
            "Usage: /computeruse <task description>\n"
            "Example: /computeruse Open Firefox and go to example.com"
        )

    task = " ".join(ctx.args)
    status_msg = await update.message.reply_text(
        f"Claude is working on: _{task}_\n\n"
        "I'll send screenshots as Claude works. This may take a moment…",
        parse_mode="Markdown",
    )

    async def forward_screenshot(img_b64: str) -> None:
        """Send interim screenshot to the Telegram chat."""
        try:
            img_bytes = base64.b64decode(img_b64)
            await update.message.reply_photo(photo=img_bytes, caption="Claude's view")
        except Exception:
            pass

    try:
        final_text = await run_computer_use_agent(task, on_screenshot=forward_screenshot)
        # Edit the status message with the final result
        await status_msg.edit_text(
            f"*Task complete:* _{task}_\n\n{final_text[:3800]}",
            parse_mode="Markdown",
        )
    except Exception as exc:
        log.exception("Computer use error: %s", exc)
        await status_msg.edit_text(f"[!] Computer use error: {exc}")


async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Unknown command. Use /help to see available commands.")


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("whois", whois_cmd))
    app.add_handler(CommandHandler("dns", dns_cmd))
    app.add_handler(CommandHandler("nmap", nmap_cmd))
    app.add_handler(CommandHandler("nikto", nikto_cmd))
    app.add_handler(CommandHandler("sqlmap", sqlmap_cmd))
    app.add_handler(CommandHandler("gobuster", gobuster_cmd))
    app.add_handler(CommandHandler("hash", hash_cmd))
    app.add_handler(CommandHandler("screenshot", screenshot_cmd))
    app.add_handler(CommandHandler("computeruse", computeruse_cmd))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    log.info("Bottel Kali bot starting…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
