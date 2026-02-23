# Social Media Automation Skills

Multi-platform social media automation: drafting, scheduling, posting, and engagement tracking across Twitter/X, LinkedIn, Threads, and Bluesky.

## Available Commands

- `/post-social` — Create and publish platform-optimized posts
- `/social-schedule` — Schedule posts to a queue with optimal timing
- `/social-monitor` — Monitor mentions, replies, and engagement metrics
- `/content-calendar` — Generate a week/month of content ideas and drafts

## Platform Coverage

| Platform | API Support | Browser Fallback | Rate Limits |
|----------|-------------|-----------------|-------------|
| Twitter/X | OAuth 2.0 via tweepy | Playwright | 50 posts/day (free tier) |
| LinkedIn | API v2 | Playwright | 150 posts/day |
| Threads | Meta Threads API | Playwright | 250 posts/day |
| Bluesky | atproto SDK | N/A | Unlimited (self-hosted relay) |

## Quick Start

```bash
pip install tweepy atproto python-linkedin-v2 playwright python-dotenv
npx playwright install chromium
cp .env.example .env  # fill in your API keys
```

## Sources

- [alekspetrov/navigator social-media-post](https://claude-plugins.dev/skills/@alekspetrov/navigator/social-media-post)
- [typefully/typefully](https://typefully.com)
- [Twitter MCP for Claude Code](https://github.com/vidhupv/x-mcp)
