# Available Skills

Skills are modular capabilities that extend what the agent can do. Each skill is defined in `skills/<name>/skill.md`.

## Core Skills

### /poster
**Purpose:** Post content to social platforms (Moltbook, X/Twitter)

```
/poster moltbook "Your post content here"
/poster x --thread
/poster all "Cross-platform post"
```

Features:
- Rate limiting enforcement
- Duplicate detection
- Markdown formatting
- Content logging

---

### /feed-reader
**Purpose:** Aggregate news and social feeds to stay informed

```
/feed-reader              # Check all sources
/feed-reader hn           # Just Hacker News
/feed-reader --summary    # Quick overview
```

Sources: Hacker News, TechCrunch, X Timeline, Moltbook Feed, CoinGecko

---

### /memory-sync
**Purpose:** Persist and recall context between sessions

```
/memory-sync save         # Save current context
/memory-sync load         # Load at session start
/memory-sync status       # Show memory state
```

Files managed:
- `memory/context.md` - Current state
- `memory/learnings.md` - Accumulated knowledge
- `memory/content-log.md` - Post history

---

### /code-shipper
**Purpose:** Build and share code, tools, and demos

```
/code-shipper create --name "project" --description "What it does"
/code-shipper ship        # Push current project
/code-shipper gist "Quick snippet"
```

Supports: GitHub repos, gists, Vercel/Netlify deploys

---

### /content-studio
**Purpose:** Create videos, images, and text content

```
/content-studio video "Topic for video"
/content-studio image "Description of image"
/content-studio thread "Topic for thread"
```

Generates: Video scripts, image prompts, long-form content

---

### /market-intel
**Purpose:** Track markets, trends, and opportunities

```
/market-intel crypto      # Crypto market overview
/market-intel trending    # What's trending
/market-intel --summary   # Quick market summary
```

Tracks: Crypto prices, market sentiment, trending topics

---

## Utility Skills

### /evolution
**Purpose:** Self-reflection and growth tracking

```
/evolution log "What I learned today"
/evolution status         # Show evolution progress
```

Maintains: `evolution/log.md` - Agent's growth journal

---

### /ping-austin
**Purpose:** Send async email to Austin for urgent issues

```
/ping-austin "Subject" "Message body"
```

Use sparingly - for urgent blockers only.

---

### /screenshot
**Purpose:** Capture and upload screenshots

```
/screenshot https://example.com
```

Captures URL, uploads to R2, returns public link.

---

### /daily-briefing
**Purpose:** Generate daily status briefing

```
/daily-briefing
```

Summarizes: Metrics, activity, priorities for the day.

---

## Creating New Skills

1. Create directory: `skills/<skill-name>/`
2. Add `skill.md` with frontmatter:

```yaml
---
name: skill-name
description: What the skill does
user_invocable: true
---
```

3. Document purpose, invocation, workflow
4. Add to CLAUDE.md skill table

## Skill Guidelines

- Keep skills focused (one job)
- Document clearly with examples
- Log all significant actions
- Respect rate limits
- Update context.md when appropriate
