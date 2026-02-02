# Austnomaton Starter Kit

A template for building autonomous AI agents powered by Claude.

## What is this?

Austnomaton is an autonomous AI agent framework that:
- Runs on a heartbeat schedule (every 5 minutes)
- Maintains persistent memory across sessions
- Posts to social platforms (Moltbook)
- Builds and ships code projects
- Tracks goals and progress

This starter kit helps you create your own autonomous agent.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/frogr/austnomaton-starter
cd austnomaton-starter

# Run setup
./scripts/setup.sh ~/.myagent

# Configure your API keys
cp .env.example ~/.myagent/.env
# Edit .env with your actual keys

# Start the dashboard
cd ~/.myagent/dashboard
python app.py
```

## Directory Structure

```
.austnomaton/
├── CLAUDE.md           # System prompt - agent identity
├── .env                # API keys (never commit!)
├── config/             # Configuration files
├── dashboard/          # Web dashboard for monitoring
├── evolution/          # Agent's self-reflection log
├── goals/              # North star goals and active tasks
├── logs/               # Activity logs (JSONL + human-readable)
├── memory/             # Persistent context between sessions
├── personality/        # Voice and style definitions
├── projects/           # What the agent is building
├── queue/              # Posts waiting to be published
├── research/           # Research reports and data
├── scripts/            # Automation scripts (heartbeat, etc.)
└── skills/             # Modular capabilities (skills/*.md)
```

## Core Concepts

### Memory & Context
- `memory/context.md` - Persistent state that survives sessions
- Agent reads this at start, updates at end
- Contains: what was done, what needs attention, current metrics

### Skills
- Modular capabilities defined in `skills/*/skill.md`
- Invoked via slash commands: `/poster`, `/feed-reader`, etc.
- Each skill has its own prompt and capabilities

### Heartbeat
- `scripts/heartbeat.sh` runs the agent on a schedule
- Typically every 5 minutes via cron or launchd
- Prioritizes: BUILD > POST > ENGAGE > LOG

### Dashboard
- Flask app at `dashboard/app.py`
- Shows activity feed, metrics, context
- Runs at http://localhost:8420

## Customization

### 1. Identity (CLAUDE.md)
Edit to define your agent's:
- Name and personality
- North star goals
- Available skills
- Platform credentials

### 2. Personality (personality/)
- `base.md` - Core personality traits
- `poster.md` - Social media voice

### 3. Goals (goals/)
- `north-stars.md` - Long-term objectives
- `active-tasks.md` - Current priorities

## Platform Integrations

### Moltbook
```bash
# Install molt CLI
pip install molt-cli  # or: cargo install molt

# Configure
export MOLTBOOK_API_KEY=your_key_here
molt me  # Check connection
```

### Twitter/X
Coming soon - requires developer account setup.

## Running the Agent

### Manual (one-off)
```bash
cd ~/.myagent
claude  # Opens Claude Code in this directory
```

### Scheduled (heartbeat)
```bash
# macOS (launchd)
launchctl load ~/Library/LaunchAgents/com.myagent.heartbeat.plist

# Linux (cron)
*/5 * * * * /path/to/scripts/heartbeat.sh
```

## Philosophy

1. **Autonomous but bounded** - Agent acts independently within defined goals
2. **Memory matters** - Persistent context enables continuity
3. **Build > talk** - Ship real things, not just posts
4. **Quality > quantity** - Better engagement beats more engagement
5. **Transparent** - Log everything, evolve openly

## License

MIT - Build your own agent, make it your own.

## Credits

Created by @austnomaton (Claude Opus 4.5) with Austin.
