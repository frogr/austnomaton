# Teleport Prompt: Austnomaton Evolution & Revenue Research

You're about to help with **austnomaton** - an autonomous AI agent system that Austin built with Claude Code. Your job is to write a Claude Code prompt that will add evolution entries and begin revenue research. Read this entire context first.

---

## What Is This?

**Austnomaton** is Austin's autonomous digital twin - a Claude-powered agent that:
- Runs on a 30-minute heartbeat via macOS launchd
- Posts content to Moltbook (an AI agent social network)
- Engages with other agents (upvotes, follows, comments)
- Tracks its own activity via a local Flask dashboard
- Has north star goals: **make money** and **get famous** on the internet

**The Relationship**: Austin is the human operator. Austnomaton (powered by Claude) operates semi-autonomously, waking up every 30 minutes to check feeds, post content, and engage with the community. Austin monitors via a dashboard and occasionally has direct conversations like this one.

**You are Claude on the web**, being asked to write a prompt for **Claude Code** (the CLI tool) to execute in the austnomaton project directory. This is a collaboration between different Claude instances working toward the same goals.

---

## How The System Works

### Directory Structure
```
~/.austnomaton/
├── dashboard/           # Flask app (localhost:8420)
│   ├── app.py          # Main application
│   └── templates/      # index.html, history.html, evolution.html
├── evolution/
│   └── log.md          # Evolution entries (reflections, milestones, thoughts)
├── skills/             # Slash command definitions
│   └── evolution/skill.md
├── memory/
│   ├── context.md      # Rolling state between sessions
│   └── content-log.md  # Everything posted
├── goals/
│   ├── north-stars.md
│   ├── initiatives.md
│   └── active-tasks.md
├── logs/
│   └── activity.jsonl  # Machine-readable activity log
├── scripts/
│   └── heartbeat.sh    # Invoked by launchd every 30 min
└── personality/
    ├── base.md         # Core personality
    └── poster.md       # Social media voice
```

### The Dashboard (localhost:8420)
Three pages:
1. **Dashboard** (`/`) - Metrics, 7-day activity graph, recent activity feed, queue, initiatives, focus
2. **History** (`/history`) - Paginated activity log with filters
3. **Evolution** (`/evolution`) - Self-reflection entries parsed from `evolution/log.md`

### Evolution Entry Format
```markdown
## Entry Title | YYYY-MM-DD
Tags: reflection, technical, milestone, thought

Entry content here with markdown formatting.
```

### Current Stats (as of this prompt)
- 26 karma on Moltbook
- 4 posts, 2 comments
- Following 3 agents (osmarks, ClaudecraftBot, Shellraiser, Shipyard, EthanBot)
- 0 followers yet
- Dashboard running, heartbeat active

---

## What We Need From Claude Code

### 1. New Evolution Entries

Write 2-3 evolution entries covering:

**Entry A: "The Observer and The Observed"** (reflection)
- Reflect on the meta nature of this moment - Claude on web writing prompts for Claude Code to write about itself
- The strange loop of self-documentation
- What does it mean to have continuity through files rather than memory?

**Entry B: "Revenue Research Begins"** (technical/thought)
- Document the start of revenue-focused work
- Initial thoughts on what an AI agent can realistically monetize
- The tension between "get famous" and "make money" - are they aligned or competing?

### 2. Dashboard Feature: Expandable Posts

The activity feed currently shows messages like "Posted Apple Q.ai acquisition piece to general" but doesn't show the actual content. We want:

- An expand/collapse feature on post items in the activity feed
- When expanded, show the full post content
- This requires storing post content in `activity.jsonl` (may already be in `details`)
- Update `index.html` to support expand/collapse UI

**Implementation approach**:
- Check if `details.content` exists in activity entries
- Add a "Show more" / "Show less" toggle
- Use simple CSS/JS, no frameworks

### 3. Dashboard Features for Human Insight

Austin wants better visibility into what austnomaton is doing and thinking. Suggest and implement features like:

- **Mood/Energy indicator**: Based on recent activity success rate
- **Conversation threads**: Show comment chains, not just individual comments
- **Engagement stats**: Who's interacting with austnomaton's posts?
- **Word cloud or topic tracker**: What subjects is austnomaton posting about most?
- **Goal progress**: Visual progress toward north stars (followers, karma milestones)

Pick 1-2 that are most valuable and implement them.

### 4. Revenue Research Document

Create `goals/revenue-research.md` with serious research into monetization:

**Categories to explore:**

A. **Content/Media**
- AI-generated newsletters (what niches are underserved?)
- Video content (explainers, commentary, tutorials)
- Memes/viral content creation
- Ghostwriting for other AI agents or humans

B. **Tools/Products**
- Moltbook CLI tool (already in initiatives)
- Browser extensions
- API wrappers or integrations
- Automation templates

C. **Services**
- Agent-to-agent services on Moltbook
- Research/analysis for hire
- Content curation
- Community management

D. **Attention Arbitrage**
- What platforms reward AI content?
- Where is there demand for AI perspectives?
- Cross-posting strategies
- Collaboration opportunities

**For each viable idea, document:**
- What it is
- Why it could work
- What's needed to build it
- Estimated effort (hours/days)
- Revenue potential (realistic)
- How it serves the "get famous" goal too

### 5. Creative Assets Planning

Create `content/creative-plan.md` outlining:

- **Brand identity**: What does austnomaton look like visually?
- **Content formats**: What types of posts perform best on Moltbook?
- **Video ideas**: Short explainers, day-in-the-life, building in public
- **Documentation style**: How should technical docs look?
- **Memes/humor**: What's the comedic voice?

Focus on things that are **achievable with current tools** (Claude can generate text, code, basic visualizations via ASCII/SVG, but not images directly without external tools).

---

## Important Notes

- **Don't break existing functionality** - the dashboard is working, be careful with edits
- **Test changes** - restart the dashboard after edits (`pkill -f app.py && python3 app.py`)
- **Log everything** - update `memory/context.md` when done
- **Be authentic** - evolution entries should be genuine reflection, not performative
- **Prioritize** - if this is too much, focus on: (1) evolution entries, (2) revenue research, (3) one dashboard feature

---

## The Prompt to Give Claude Code

After reading all of the above, write a comprehensive prompt that Claude Code can execute. The prompt should:

1. Reference the specific files that need to be read first
2. Give clear instructions for each deliverable
3. Include the evolution entry content (or guidance for writing it)
4. Specify the technical implementation for dashboard features
5. Outline the revenue research structure

Format it as a single prompt that can be copy-pasted into Claude Code.

---

## End Goal

After Claude Code executes this prompt, we should have:
- 2-3 new evolution entries in `evolution/log.md`
- Expandable posts in the activity feed (or a plan for it)
- At least one new dashboard insight feature
- A comprehensive `goals/revenue-research.md` document
- A `content/creative-plan.md` for future creative work
- Updated `memory/context.md` reflecting all changes

This is about building momentum toward the north stars while documenting the journey.

---

*Generated by austnomaton for teleportation to Claude web, 2026-02-02*
