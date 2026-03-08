"""
computer_use.py – Computer Use agent for the Kali Linux Telegram bot.

Uses the Anthropic Computer Use tool (computer_20251124) with claude-opus-4-6
to let Claude see the Kali desktop and control it autonomously.

Desktop actions are executed locally via xdotool + scrot inside the container.
"""

import asyncio
import base64
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import anthropic

log = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
DISPLAY = os.environ.get("DISPLAY", ":1")
DISPLAY_W = int(os.environ.get("DISPLAY_WIDTH", "1280"))
DISPLAY_H = int(os.environ.get("DISPLAY_HEIGHT", "800"))
MAX_ITERATIONS = 20          # Safety cap on the agent loop
TOOL_VERSION = "computer_20251124"
BETA_FLAG = "computer-use-2025-11-24"

client = anthropic.AsyncAnthropic()


# ── Screenshot ─────────────────────────────────────────────────────────────────
async def take_screenshot() -> str:
    """Capture the current display and return a base64-encoded PNG."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        path = tmp.name

    try:
        proc = await asyncio.create_subprocess_exec(
            "scrot", "--silent", path,
            env={**os.environ, "DISPLAY": DISPLAY},
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.communicate(), timeout=10)
        data = Path(path).read_bytes()
        return base64.standard_b64encode(data).decode()
    finally:
        Path(path).unlink(missing_ok=True)


# ── Action dispatcher ──────────────────────────────────────────────────────────
async def execute_action(action: str, params: dict) -> dict:
    """
    Translate Claude's computer_use tool_use request into real system calls.
    Returns the tool_result content block for the next API message.
    """
    env = {**os.environ, "DISPLAY": DISPLAY}

    async def run(*cmd):
        proc = await asyncio.create_subprocess_exec(
            *cmd, env=env,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.communicate(), timeout=15)

    try:
        if action == "screenshot":
            img_b64 = await take_screenshot()
            return {
                "type": "tool_result_content",
                "output": {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64,
                    },
                },
            }

        elif action == "left_click":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            await run("xdotool", "click", "1")

        elif action == "right_click":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            await run("xdotool", "click", "3")

        elif action == "double_click":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            await run("xdotool", "click", "--repeat", "2", "1")

        elif action == "triple_click":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            await run("xdotool", "click", "--repeat", "3", "1")

        elif action == "middle_click":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            await run("xdotool", "click", "2")

        elif action == "mouse_move":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))

        elif action == "left_click_drag":
            sx, sy = params["start_coordinate"]
            ex, ey = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(sx), str(sy))
            await run("xdotool", "mousedown", "1")
            await asyncio.sleep(0.1)
            await run("xdotool", "mousemove", "--sync", str(ex), str(ey))
            await run("xdotool", "mouseup", "1")

        elif action == "left_mouse_down":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            await run("xdotool", "mousedown", "1")

        elif action == "left_mouse_up":
            x, y = params["coordinate"]
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            await run("xdotool", "mouseup", "1")

        elif action == "scroll":
            x, y = params["coordinate"]
            direction = params.get("direction", "down")
            amount = int(params.get("amount", 3))
            button = "4" if direction in ("up", "left") else "5"
            await run("xdotool", "mousemove", "--sync", str(x), str(y))
            for _ in range(amount):
                await run("xdotool", "click", button)

        elif action == "type":
            text = params["text"]
            await run("xdotool", "type", "--clearmodifiers", "--delay", "20", text)

        elif action == "key":
            key = params["text"]
            await run("xdotool", "key", "--clearmodifiers", key)

        elif action == "hold_key":
            key = params["text"]
            duration = float(params.get("duration", 0.5))
            await run("xdotool", "keydown", key)
            await asyncio.sleep(duration)
            await run("xdotool", "keyup", key)

        elif action == "wait":
            duration = float(params.get("duration", 1.0))
            await asyncio.sleep(min(duration, 10.0))

        elif action == "zoom":
            # Zoom: take a screenshot and crop to the specified region
            region = params.get("region", [0, 0, DISPLAY_W, DISPLAY_H])
            x1, y1, x2, y2 = region
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                path = tmp.name
            try:
                proc = await asyncio.create_subprocess_exec(
                    "scrot", "--silent",
                    "--area", f"{x1},{y1},{x2 - x1},{y2 - y1}",
                    path,
                    env=env,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(proc.communicate(), timeout=10)
                data = Path(path).read_bytes()
                img_b64 = base64.standard_b64encode(data).decode()
            finally:
                Path(path).unlink(missing_ok=True)

            return {
                "type": "tool_result_content",
                "output": {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64,
                    },
                },
            }

        else:
            log.warning("Unknown action: %s", action)
            return {"type": "tool_result_content", "output": f"Unknown action: {action}"}

        return {"type": "tool_result_content", "output": "Action completed."}

    except asyncio.TimeoutError:
        return {"type": "tool_result_content", "output": "Action timed out.", "is_error": True}
    except Exception as exc:
        log.exception("Action error: %s", exc)
        return {"type": "tool_result_content", "output": f"Error: {exc}", "is_error": True}


# ── Agent loop ─────────────────────────────────────────────────────────────────
async def run_computer_use_agent(
    task: str,
    on_screenshot: "asyncio.coroutines.CoroutineType | None" = None,
) -> str:
    """
    Run the computer-use agent loop for the given `task`.

    `on_screenshot` is an optional async callback invoked with a base64 PNG
    string each time Claude takes a screenshot — useful for forwarding
    interim screenshots to the Telegram chat.

    Returns Claude's final text response.
    """
    tools = [
        {
            "type": TOOL_VERSION,
            "name": "computer",
            "display_width_px": DISPLAY_W,
            "display_height_px": DISPLAY_H,
            "display_number": int(DISPLAY.lstrip(":")),
            "enable_zoom": True,
        }
    ]

    system = (
        "You are a cybersecurity assistant controlling a Kali Linux desktop. "
        "Use the computer tool to complete the requested task. "
        "Always take a screenshot first to see the current state. "
        "Only perform actions on systems you have explicit permission to test."
    )

    messages: list[dict] = [{"role": "user", "content": task}]
    final_text = ""

    for iteration in range(MAX_ITERATIONS):
        log.info("Computer-use iteration %d/%d", iteration + 1, MAX_ITERATIONS)

        response = await client.beta.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=system,
            tools=tools,
            messages=messages,
            betas=[BETA_FLAG],
        )

        # Collect text from this turn
        for block in response.content:
            if hasattr(block, "type") and block.type == "text":
                final_text = block.text

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        # If no tool use, we're done
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            break

        # Execute each tool call and collect results
        tool_results = []
        for tu in tool_use_blocks:
            action = tu.input.get("action", "")
            result = await execute_action(action, tu.input)

            # Notify caller of screenshot
            if action in ("screenshot", "zoom") and on_screenshot:
                output = result.get("output", {})
                if isinstance(output, dict) and output.get("type") == "image":
                    img_b64 = output["source"]["data"]
                    try:
                        await on_screenshot(img_b64)
                    except Exception:
                        pass

            # Build tool_result content
            output = result.get("output", "")
            if isinstance(output, dict) and output.get("type") == "image":
                content = [output]
            else:
                content = str(output)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": content,
                **({"is_error": True} if result.get("is_error") else {}),
            })

        messages.append({"role": "user", "content": tool_results})

    else:
        log.warning("Computer-use agent hit iteration limit (%d)", MAX_ITERATIONS)
        final_text = (final_text or "") + f"\n\n[Reached max iterations ({MAX_ITERATIONS})]"

    return final_text or "Task completed."
