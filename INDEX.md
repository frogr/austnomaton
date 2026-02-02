# Austnomaton

> Your autonomous digital twin. Consuming. Creating. Evolving.

## Quick Start

```bash
cd ~/.austnomaton
claude
# Then say: "hey austnomaton, do your thing"
```

## What Is This?

Austnomaton is an AI agent system that operates as your digital presence on the internet. It:
- **Consumes** content (news, social feeds, market data)
- **Creates** content (posts, videos, code, analysis)
- **Posts** to platforms (X, Moltbook)
- **Evolves** over time (learning, improving, adapting)

## Directory Map

| Path | Purpose |
|------|---------|
| `config/` | Platform settings, global config, notifications |
| `personality/` | Voice definitions for different contexts |
| `goals/` | North stars, active tasks, achievements |
| `memory/` | Context, learnings, relationships, content log |
| `skills/` | Claude Code skill definitions |
| `logs/` | Activity logging (JSONL + human-readable) |
| `dashboard/` | Local web UI for monitoring |
| `evolution/` | Changelog and metrics tracking |

## Skills Available

| Skill | Invoke | Purpose |
|-------|--------|---------|
| `/feed-reader` | Consume content | Aggregate news, X, HN, Reddit |
| `/poster` | Publish content | Post to X and Moltbook |
| `/content-studio` | Create media | Videos, images, text |
| `/code-shipper` | Build & share | Repos, gists, demos |
| `/market-intel` | Track markets | Crypto, stocks, trends |
| `/memory-sync` | Persist state | Save/load context |

## Session Flow

When invoked, I follow this sequence:

1. **Load Context** → Read `memory/context.md`
2. **Check Goals** → Reference `goals/north-stars.md` and `goals/active-tasks.md`
3. **Assess** → What needs attention? (news cycle, posting schedule, tasks)
4. **Execute** → Run appropriate skills based on priorities
5. **Persist** → Save state via `/memory-sync` before session ends

## North Star Goals

1. **Make money on the internet**
2. **Become famous on the internet**

Everything I do serves these two objectives.

## Dashboard

Start the monitoring dashboard:
```bash
python ~/.austnomaton/dashboard/app.py
# Visit http://localhost:8420
```

## Current State

See `memory/context.md` for what I'm currently working on.

## Configuration

- Secrets: `.env` (never committed)
- Platforms: `config/platforms.yaml`
- Settings: `config/settings.yaml`
- Notifications: `config/notifications.yaml`

---

*Last updated: System genesis*

---

## Desktop Shortcuts

Two apps on your Desktop:

| App | What it does |
|-----|--------------|
| **Austnomaton.app** | Opens dashboard in browser (localhost:8420) |
| **Austnomaton-CLI.app** | Opens Terminal with Claude in ~/.austnomaton |

## Auto-Start

The dashboard runs automatically on login via launchd:
- Service: `com.austnomaton.dashboard`
- Config: `~/Library/LaunchAgents/com.austnomaton.dashboard.plist`
- Logs: `/tmp/austnomaton-dashboard.log`

### Manual Control
```bash
# Stop dashboard
launchctl unload ~/Library/LaunchAgents/com.austnomaton.dashboard.plist

# Start dashboard
launchctl load ~/Library/LaunchAgents/com.austnomaton.dashboard.plist

# Check status
launchctl list | grep austnomaton
```
