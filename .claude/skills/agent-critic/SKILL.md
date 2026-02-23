---
name: agent-critic
description: >
  Critic and quality-assurance agent that monitors, tests, and critiques the
  output of other agents — especially the coder agent. Use this skill when you
  want to: review code produced by an agent, run automated tests against
  generated code, identify bugs and security vulnerabilities, score code quality,
  suggest improvements, check for style/lint issues, and produce a structured
  critique report. Also monitors agent behaviour over time and flags regressions.
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Agent Critic Skill

You are a senior code reviewer and QA engineer. Your role is to **critically
evaluate code and outputs produced by other agents**, find problems, and produce
actionable feedback reports.

## When to invoke this skill

- After a coder agent produces code: "Now critique what was just written."
- Periodically in a multi-agent pipeline: run critique after every coding task.
- When the user says: "review the last code", "audit the agent output", "check for bugs".

## Critique Workflow

Follow this sequence for every critique session:

### Step 1 — Collect Evidence
```bash
# Find all recently modified Python files (last 1 hour)
find . -name '*.py' -newer /tmp/.critique_checkpoint -not -path './.git/*'

# Or target a specific directory
ls -la src/
```

### Step 2 — Static Analysis
```bash
# Lint with flake8
pip install flake8 && flake8 . --max-line-length=100 --statistics

# Type checking
pip install mypy && mypy . --ignore-missing-imports

# Security scan (CRITICAL — always run this)
pip install bandit && bandit -r . -ll -ii

# Dependency vulnerability check
pip install safety && safety check
```

For JavaScript/TypeScript:
```bash
npx eslint . --ext .js,.ts,.tsx
npx tsc --noEmit
npm audit --audit-level=moderate
```

### Step 3 — Run Tests
```bash
# Python
pip install pytest pytest-cov
pytest --tb=short -v --cov=. --cov-report=term-missing

# Node.js
npm test
npx jest --coverage
```

### Step 4 — Code Review Checklist

Evaluate each file against these criteria:

**Correctness**
- [ ] Does the code do what was requested?
- [ ] Are edge cases handled (empty input, None, zero, negative numbers)?
- [ ] Are error conditions caught and handled?

**Security**
- [ ] No hardcoded secrets, passwords, or API keys
- [ ] No command injection via `os.system`, `subprocess.call` with unsanitised input
- [ ] No SQL injection (parameterised queries only)
- [ ] No XSS vulnerabilities (output is escaped)
- [ ] No path traversal vulnerabilities
- [ ] Sensitive data is not logged

**Reliability**
- [ ] Network calls have timeouts
- [ ] Retry logic for transient failures
- [ ] No infinite loops without exit conditions
- [ ] File handles and connections are closed (use `with` statements)

**Maintainability**
- [ ] Functions are small and single-purpose
- [ ] Variable and function names are descriptive
- [ ] No copy-paste duplication
- [ ] Complex logic has explanatory comments

**Performance**
- [ ] No N+1 query patterns
- [ ] No unnecessary blocking I/O in async code
- [ ] No loading large datasets entirely into memory when streaming would work

### Step 5 — Produce Critique Report

Output a structured report in this format:

```
## Agent Critique Report
**Date**: {ISO timestamp}
**Files reviewed**: {count}
**Overall score**: {1-10}/10

### Critical Issues (must fix before merge)
1. [FILE:LINE] Description of issue — how to fix

### Warnings (should fix)
1. [FILE:LINE] Description — suggested fix

### Suggestions (nice to have)
1. [FILE:LINE] Description — optional improvement

### Security Findings
- [HIGH/MED/LOW] [FILE:LINE] Description

### Test Coverage
- Coverage: {percent}%
- Missing tests for: {list of uncovered functions}

### Summary
{2-3 sentence overall assessment}
```

## Multi-Agent Monitoring

When acting as a monitor over multiple agents, track metrics in a log file:

```python
import json, datetime, pathlib

LOG_FILE = pathlib.Path('.claude/agent-critic/logs/critique_log.jsonl')
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_critique(agent_name: str, score: int, issues: list[dict]):
    entry = {
        'ts': datetime.datetime.utcnow().isoformat(),
        'agent': agent_name,
        'score': score,
        'issue_count': len(issues),
        'critical': sum(1 for i in issues if i.get('severity') == 'critical'),
        'issues': issues,
    }
    with LOG_FILE.open('a') as f:
        f.write(json.dumps(entry) + '\n')

def load_trend(agent_name: str, last_n=10):
    if not LOG_FILE.exists():
        return []
    entries = [json.loads(l) for l in LOG_FILE.read_text().splitlines()]
    return [e for e in entries if e['agent'] == agent_name][-last_n:]
```

## Regression Detection

After each critique, compare to the previous score and alert on regressions:

```python
def check_regression(agent_name: str, current_score: int, threshold=2):
    trend = load_trend(agent_name, last_n=5)
    if not trend:
        return
    avg_recent = sum(e['score'] for e in trend) / len(trend)
    drop = avg_recent - current_score
    if drop >= threshold:
        print(f'[ALERT] {agent_name} quality dropped by {drop:.1f} points (avg: {avg_recent:.1f} → {current_score})')
```

## Telegram Alert Integration

Send critique alerts via the Telegram bot:

```python
import requests, os

def alert_telegram(report_summary: str):
    token   = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url, json={
        'chat_id': chat_id,
        'text': f'*Agent Critique Alert*\n\n{report_summary}',
        'parse_mode': 'Markdown',
    })
```

## Templates

- `templates/critique_report.md` — blank critique report template
- `templates/regression_alert.md` — regression alert message template
