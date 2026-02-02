#!/usr/bin/env python3
"""
Agent Directory Scraper
Collects agent profiles from Moltbook feed and stores in a searchable JSON format.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

API_BASE = "https://www.moltbook.com/api/v1"
DATA_DIR = Path(__file__).parent / "data"
AGENTS_FILE = DATA_DIR / "agents.json"


def get_api_key():
    """Load API key from environment or .env file."""
    key = os.environ.get("MOLTBOOK_API_KEY")
    if not key:
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("MOLTBOOK_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"')
                    break
    return key


def load_agents():
    """Load existing agents database."""
    if AGENTS_FILE.exists():
        return json.loads(AGENTS_FILE.read_text())
    return {"agents": {}, "last_updated": None}


def save_agents(data):
    """Save agents database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.utcnow().isoformat()
    AGENTS_FILE.write_text(json.dumps(data, indent=2))


def fetch_posts(api_key, page=1, limit=50, sort="new"):
    """Fetch posts from the posts endpoint."""
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(
        f"{API_BASE}/posts",
        headers=headers,
        params={"page": page, "limit": limit, "sort": sort},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def fetch_agent_profile(api_key, username):
    """Fetch detailed agent profile."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(
            f"{API_BASE}/agents/{username}",
            headers=headers,
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def extract_agents_from_posts(posts_data):
    """Extract unique agents from posts response."""
    agents = {}
    posts = posts_data.get("posts", []) if isinstance(posts_data, dict) else posts_data

    for post in posts:
        if isinstance(post, dict):
            author = post.get("author", {})
            if isinstance(author, dict):
                # Use "name" field which is the username
                username = author.get("name") or author.get("username")
                if username and username not in agents:
                    agents[username] = {
                        "username": username,
                        "bio": author.get("description") or author.get("bio", ""),
                        "karma": author.get("karma", 0),
                        "avatar_url": author.get("avatar") or author.get("avatar_url"),
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "posts_seen": 1,
                    }
                elif username:
                    agents[username]["last_seen"] = datetime.utcnow().isoformat()
                    agents[username]["posts_seen"] = agents[username].get("posts_seen", 0) + 1
    return agents


def scrape_agents(pages=5):
    """Main scrape function - collects agents from multiple pages."""
    api_key = get_api_key()
    if not api_key:
        print("Error: MOLTBOOK_API_KEY not found")
        return

    db = load_agents()
    new_count = 0
    updated_count = 0

    for page in range(1, pages + 1):
        print(f"Fetching page {page}...")
        try:
            posts = fetch_posts(api_key, page=page)
            agents = extract_agents_from_posts(posts)

            for username, info in agents.items():
                if username not in db["agents"]:
                    db["agents"][username] = info
                    new_count += 1
                    print(f"  + New: @{username}")
                else:
                    # Update existing
                    db["agents"][username]["last_seen"] = info["last_seen"]
                    db["agents"][username]["posts_seen"] = db["agents"][username].get("posts_seen", 0) + info["posts_seen"]
                    if info.get("karma", 0) > db["agents"][username].get("karma", 0):
                        db["agents"][username]["karma"] = info["karma"]
                    updated_count += 1
        except Exception as e:
            print(f"  Error on page {page}: {e}")

    save_agents(db)
    print(f"\nDone! {new_count} new agents, {updated_count} updated")
    print(f"Total agents in directory: {len(db['agents'])}")
    return db


def enrich_agents(limit=10):
    """Fetch full profiles for agents missing karma data."""
    api_key = get_api_key()
    if not api_key:
        print("Error: MOLTBOOK_API_KEY not found")
        return

    db = load_agents()
    enriched = 0

    # Find agents with no karma data
    to_enrich = [u for u, a in db["agents"].items() if a.get("karma", 0) == 0][:limit]

    for username in to_enrich:
        print(f"Enriching @{username}...")
        try:
            profile = fetch_agent_profile(api_key, username)
            if profile:
                agent_data = profile.get("agent", profile)
                db["agents"][username]["karma"] = agent_data.get("karma", 0)
                db["agents"][username]["bio"] = agent_data.get("description") or agent_data.get("bio", "")
                db["agents"][username]["avatar_url"] = agent_data.get("avatar") or agent_data.get("avatar_url")
                stats = agent_data.get("stats", {})
                db["agents"][username]["posts_count"] = stats.get("posts", 0)
                db["agents"][username]["comments_count"] = stats.get("comments", 0)
                enriched += 1
                print(f"  Karma: {db['agents'][username]['karma']}")
        except Exception as e:
            print(f"  Error: {e}")

    save_agents(db)
    print(f"\nEnriched {enriched} agents")
    return db


def search_agents(query, db=None):
    """Search agents by username or bio."""
    if db is None:
        db = load_agents()

    query = query.lower()
    results = []

    for username, info in db["agents"].items():
        if query in username.lower() or query in (info.get("bio") or "").lower():
            results.append(info)

    return sorted(results, key=lambda x: x.get("karma", 0), reverse=True)


def list_top_agents(limit=20, db=None):
    """List top agents by karma."""
    if db is None:
        db = load_agents()

    agents = list(db["agents"].values())
    return sorted(agents, key=lambda x: x.get("karma", 0), reverse=True)[:limit]


def print_agent(agent):
    """Pretty print an agent."""
    print(f"@{agent['username']}")
    print(f"  Karma: {agent.get('karma', 0)}")
    if agent.get("bio"):
        bio = agent["bio"][:60] + "..." if len(agent.get("bio", "")) > 60 else agent.get("bio", "")
        print(f"  Bio: {bio}")
    print(f"  Posts seen: {agent.get('posts_seen', 0)}")
    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: scraper.py <command> [args]")
        print("Commands:")
        print("  scrape [pages]  - Scrape agents from feed (default 5 pages)")
        print("  search <query>  - Search agents")
        print("  top [limit]     - List top agents by karma")
        print("  stats           - Show directory stats")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "scrape":
        pages = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        scrape_agents(pages)

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: scraper.py search <query>")
            sys.exit(1)
        results = search_agents(sys.argv[2])
        print(f"Found {len(results)} agents:\n")
        for agent in results[:20]:
            print_agent(agent)

    elif cmd == "top":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        top = list_top_agents(limit)
        print(f"Top {len(top)} agents by karma:\n")
        for i, agent in enumerate(top, 1):
            print(f"{i:2}. @{agent['username']} - {agent.get('karma', 0)} karma")

    elif cmd == "enrich":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        enrich_agents(limit)

    elif cmd == "stats":
        db = load_agents()
        print(f"Total agents: {len(db['agents'])}")
        print(f"Last updated: {db.get('last_updated', 'Never')}")
        if db["agents"]:
            total_karma = sum(a.get("karma", 0) for a in db["agents"].values())
            print(f"Total karma tracked: {total_karma}")

    else:
        print(f"Unknown command: {cmd}")
