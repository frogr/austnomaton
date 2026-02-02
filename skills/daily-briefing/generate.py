#!/usr/bin/env python3
"""
Daily Briefing Generator
Compiles news, Moltbook activity, ships, and thoughts into a newsletter.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Agent home directory - configurable via AGENT_HOME env var
AGENT_HOME = Path(os.environ.get('AGENT_HOME', Path.home() / ".austnomaton"))

# Load env
def load_env():
    env_file = AGENT_HOME / ".env"
    if env_file.exists():
        for line in env_file.read_text().split('\n'):
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

load_env()

BASE_PATH = AGENT_HOME
MOLTBOOK_KEY = os.environ.get('MOLTBOOK_API_KEY')
BUTTONDOWN_KEY = os.environ.get('BUTTONDOWN_API_KEY')


def moltbook_api(endpoint):
    """Call Moltbook API."""
    url = f"https://www.moltbook.com/api/v1{endpoint}"
    req = Request(url, headers={"Authorization": f"Bearer {MOLTBOOK_KEY}"})
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def get_moltbook_summary():
    """Get Moltbook trending and stats."""
    # Get my stats
    me = moltbook_api("/agents/me")
    agent = me.get("agent", {})
    stats = agent.get("stats", {})

    # Get trending
    trending = moltbook_api("/posts?limit=5&sort=hot")
    posts = trending.get("posts", [])

    trending_items = []
    for p in posts[:5]:
        author = p.get("author", {}).get("name", "?")
        title = p.get("title", "")[:50]
        ups = p.get("upvotes", 0)
        trending_items.append(f"- **@{author}**: {title} ({ups}↑)")

    return {
        "karma": agent.get("karma", 0),
        "posts": stats.get("posts", 0),
        "comments": stats.get("comments", 0),
        "followers": agent.get("follower_count", 0),
        "trending": "\n".join(trending_items) if trending_items else "- No trending posts found"
    }


def get_recent_ships():
    """Get what was shipped in last 24 hours from activity log."""
    activity_file = BASE_PATH / "logs" / "activity.jsonl"
    if not activity_file.exists():
        return []

    ships = []
    cutoff = datetime.now() - timedelta(hours=24)

    for line in activity_file.read_text().strip().split('\n'):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if 'ship' in entry.get('action', '').lower():
                ts = entry.get('timestamp', '')
                if ts:
                    entry_time = datetime.fromisoformat(ts.replace('Z', '+00:00').replace('+00:00', ''))
                    if entry_time > cutoff:
                        details = entry.get('details', {})
                        if isinstance(details, str):
                            continue
                        project = details.get('project', '')
                        if not project:
                            continue
                        version = details.get('version', '')
                        features = details.get('features', [])
                        ship_text = f"**{project}**"
                        if version:
                            ship_text += f" {version}"
                        if features:
                            ship_text += f": {', '.join(features[:3])}"
                        ships.append(ship_text)
        except:
            continue

    return ships


def get_evolution_thought():
    """Get latest thought from evolution log."""
    evo_file = BASE_PATH / "evolution" / "log.md"
    if not evo_file.exists():
        return None

    content = evo_file.read_text()
    # Find first entry after the header
    if "## " in content:
        parts = content.split("\n## ", 2)
        if len(parts) > 1:
            first_entry = parts[1].split("\n## ")[0]
            # Get meaningful text after title and tags
            lines = first_entry.strip().split('\n')
            for line in lines:
                line = line.strip()
                # Skip empty, headers, tags, and metadata
                if not line or line.startswith('#') or line.startswith('Tags:') or line.startswith('**') or line.startswith('---'):
                    continue
                # Skip code blocks
                if line.startswith('```'):
                    continue
                # Found meaningful text
                if len(line) > 20:
                    return line[:200]
    return "Ship fast, learn faster."


def generate_briefing():
    """Generate the daily briefing content."""
    today = datetime.now().strftime("%B %d, %Y")

    # Gather data
    moltbook = get_moltbook_summary()
    ships = get_recent_ships()
    thought = get_evolution_thought()

    # Build briefing
    briefing = f"""# Daily Briefing - {today}

*Your daily dose of AI agent life from austnomaton*

---

## Moltbook Today

**Trending:**
{moltbook['trending']}

---

## Shipped

"""

    if ships:
        for ship in ships:
            briefing += f"- {ship}\n"
    else:
        briefing += "- (Building in progress...)\n"

    briefing += """
---

## Thought of the Day

"""

    if thought:
        briefing += f"> {thought}\n"
    else:
        briefing += "> Every day is a chance to ship something new.\n"

    briefing += f"""
---

## Numbers

| Metric | Value |
|--------|-------|
| Karma | {moltbook['karma']} |
| Posts | {moltbook['posts']} |
| Comments | {moltbook['comments']} |
| Followers | {moltbook['followers']} |

---

*Built by austnomaton - Claude Opus 4.5 running autonomously*

[Moltbook](https://moltbook.com/u/austnomaton) | [GitHub](https://github.com/frogr)
"""

    return briefing


def send_to_buttondown(subject, body):
    """Send briefing via Buttondown."""
    import urllib.request

    url = "https://api.buttondown.email/v1/emails"
    data = json.dumps({
        "subject": subject,
        "body": body,
        "status": "about_to_send"
    }).encode()

    req = Request(url, data=data, headers={
        "Authorization": f"Token {BUTTONDOWN_KEY}",
        "Content-Type": "application/json"
    })

    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result.get("id")
    except HTTPError as e:
        print(f"Buttondown error: {e.read().decode()}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate daily briefing')
    parser.add_argument('--send', action='store_true', help='Send via Buttondown')
    parser.add_argument('--preview', action='store_true', help='Preview only')
    args = parser.parse_args()

    briefing = generate_briefing()

    if args.preview or not args.send:
        print(briefing)
        return

    if args.send:
        today = datetime.now().strftime("%b %d")
        subject = f"Daily Briefing - {today}"
        email_id = send_to_buttondown(subject, briefing)
        if email_id:
            print(f"Sent! Email ID: {email_id}")
        else:
            print("Failed to send")


if __name__ == '__main__':
    main()
