# Agent Monitoring & Orchestration Skills

A multi-agent coordination system where specialized agents monitor, test, and critique each other — ensuring code quality, correctness, and continuous improvement.

## Agent Roles

| Agent | Command | Role |
|-------|---------|------|
| **Coder Agent** | *(default Claude Code)* | Writes, refactors, and implements code |
| **Critic Agent** | `/code-critic` | Reviews coder output: correctness, quality, security, edge cases |
| **Test Agent** | `/test-agent` | Writes and runs tests against the coder's implementation |
| **Orchestrator** | `/agent-orchestrate` | Coordinates multi-agent workflows, assigns tasks, aggregates results |
| **Monitor Agent** | `/agent-monitor` | Watches all running agents, detects failures, escalates issues |

## Workflow

```
User Request
    │
    ▼
Orchestrator assigns task to Coder Agent
    │
    ▼
Coder Agent implements code
    │
    ▼
Test Agent writes + runs tests
    │
    ├─── Tests PASS ──► Critic Agent reviews code quality
    │                        │
    │                        ├─── APPROVED ──► Merge / Deploy
    │                        └─── REJECTED ──► Back to Coder with feedback
    │
    └─── Tests FAIL ──► Back to Coder with failure report
```

## Sources

- [wshobson/agents](https://github.com/wshobson/agents) — 112 specialized agents
- [jayminwest/overstory](https://github.com/jayminwest/overstory) — swarm orchestration
- [ruvnet/claude-flow](https://github.com/ruvnet/claude-flow) — multi-agent framework
- [Claude Code Agent Teams](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
