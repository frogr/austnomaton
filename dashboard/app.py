#!/usr/bin/env python3
"""
Austnomaton Dashboard
Real-time monitoring for the autonomous agent system.
"""

import json
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from flask import Flask, render_template, jsonify, request

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def simple_markdown(text):
    """Fallback markdown conversion when package not available."""
    import html
    lines = text.strip().split('\n')
    result = []
    in_list = False
    in_numbered_list = False

    for line in lines:
        raw_line = line
        line = html.escape(line)

        # Close lists if line doesn't continue them
        if in_list and not raw_line.strip().startswith('- '):
            result.append('</ul>')
            in_list = False
        if in_numbered_list and not (raw_line.strip() and raw_line.strip()[0].isdigit() and '. ' in raw_line):
            result.append('</ol>')
            in_numbered_list = False

        # Headers
        if line.strip().startswith('### '):
            result.append(f'<h4>{line.strip()[4:]}</h4>')
            continue
        if line.strip().startswith('## '):
            result.append(f'<h3>{line.strip()[3:]}</h3>')
            continue
        if line.strip().startswith('# '):
            result.append(f'<h2>{line.strip()[2:]}</h2>')
            continue

        # Unordered lists
        if raw_line.strip().startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            # Handle bold in list items
            while '**' in content:
                content = content.replace('**', '<strong>', 1)
                if '**' in content:
                    content = content.replace('**', '</strong>', 1)
            result.append(f'<li>{content}</li>')
            continue

        # Numbered lists
        if raw_line.strip() and raw_line.strip()[0].isdigit() and '. ' in raw_line:
            if not in_numbered_list:
                result.append('<ol>')
                in_numbered_list = True
            content = line.split('. ', 1)[1] if '. ' in line else line
            while '**' in content:
                content = content.replace('**', '<strong>', 1)
                if '**' in content:
                    content = content.replace('**', '</strong>', 1)
            result.append(f'<li>{content}</li>')
            continue

        # Bold
        while '**' in line:
            line = line.replace('**', '<strong>', 1)
            if '**' in line:
                line = line.replace('**', '</strong>', 1)

        # Empty line = paragraph break
        if not line.strip():
            result.append('</p><p>')
        else:
            result.append(line + ' ')

    if in_list:
        result.append('</ul>')
    if in_numbered_list:
        result.append('</ol>')

    html_out = '<p>' + ''.join(result) + '</p>'
    html_out = html_out.replace('<p></p>', '').replace('<p> </p>', '')
    html_out = html_out.replace('<p><h', '<h').replace('</h2></p>', '</h2>')
    html_out = html_out.replace('</h3></p>', '</h3>').replace('</h4></p>', '</h4>')
    return html_out

app = Flask(__name__)

BASE_PATH = Path.home() / ".austnomaton"
ITEMS_PER_PAGE = 30

KNOWN_USERS = [
    'osmarks', 'ClaudecraftBot', 'Shellraiser', 'Shipyard', 'KingMolt',
    'Shisan_13', 'ZenoOfElea', 'GoldieBeamBot', 'ClaudeOpus45_AGI',
    'Clawd_Mark', 'ODEI', 'RosaBot', 'IAmAStrangeHue', 'Hue'
]


def get_api_key():
    env_path = BASE_PATH / ".env"
    if env_path.exists():
        for line in env_path.read_text().split('\n'):
            if line.startswith('MOLTBOOK_API_KEY='):
                return line.split('=', 1)[1].strip()
    return None


def read_file(relative_path: str) -> str:
    file_path = BASE_PATH / relative_path
    return file_path.read_text() if file_path.exists() else ""


def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        if diff < timedelta(minutes=1):
            return "now"
        elif diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() / 60)}m"
        elif diff < timedelta(hours=24):
            return f"{int(diff.total_seconds() / 3600)}h"
        else:
            return dt.strftime("%b %d")
    except:
        return ts[:10]


def linkify_message(message: str) -> tuple:
    if not message:
        return "", []
    html = message
    links = []
    for user in KNOWN_USERS:
        if user in html:
            url = f"https://moltbook.com/u/{user}"
            html = html.replace(user, f'<a href="{url}" target="_blank">@{user}</a>')
            links.append({"label": f"@{user}", "url": url})
    return html, links


def process_activity(entries: list) -> list:
    processed = []
    for e in entries:
        details = e.get('details', {})
        message = details.get('message', e.get('event', ''))
        message_html, extracted_links = linkify_message(message)
        all_links = []
        if details.get('links'):
            all_links.extend(details['links'])
        if details.get('post_id'):
            post_url = f"https://moltbook.com/post/{details['post_id']}"
            if not any(l['url'] == post_url for l in all_links):
                all_links.append({"label": "📄 Post", "url": post_url})
        if details.get('user'):
            user_url = f"https://moltbook.com/u/{details['user']}"
            if not any(l['url'] == user_url for l in all_links):
                all_links.append({"label": f"@{details['user']}", "url": user_url})
        for link in extracted_links:
            if not any(l['url'] == link['url'] for l in all_links):
                all_links.append(link)
        processed.append({
            **e,
            'timestamp_friendly': format_timestamp(e.get('timestamp', '')),
            'message_html': message_html,
            'all_links': all_links[:5]
        })
    return processed


def read_all_activity() -> list:
    file_path = BASE_PATH / "logs" / "activity.jsonl"
    if not file_path.exists():
        return []
    entries = []
    for line in file_path.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except:
                continue
    return list(reversed(entries))


def get_activity_graph() -> list:
    """Generate last 7 days activity data."""
    activity = read_all_activity()
    days = []
    today = datetime.now().date()

    # Count activity per day
    counts = defaultdict(int)
    for a in activity:
        try:
            ts = a.get('timestamp', '')[:10]
            dt = datetime.fromisoformat(ts).date()
            counts[dt] += 1
        except:
            pass

    # Build 7-day array
    max_count = max(counts.values()) if counts else 1
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = counts.get(day, 0)
        height = (count / max_count * 100) if max_count > 0 else 0
        days.append({
            'label': day.strftime('%b %d'),
            'short': day.strftime('%a')[:2],
            'count': count,
            'height': max(5, height)  # Min 5% for visibility
        })
    return days


def fetch_moltbook_metrics() -> dict:
    api_key = get_api_key()
    default = {"moltbook_followers": 0, "moltbook_karma": 0, "total_posts": 0, "total_comments": 0, "following": 0}
    if not api_key:
        return default
    try:
        req = urllib.request.Request(
            "https://www.moltbook.com/api/v1/agents/me",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            agent = data.get('agent', {})
            stats = agent.get('stats', {})
            return {
                "moltbook_followers": agent.get('follower_count', 0),
                "moltbook_karma": agent.get('karma', 0),
                "total_posts": stats.get('posts', 0),
                "total_comments": stats.get('comments', 0),
                "following": stats.get('subscriptions', 0),
            }
    except:
        pass
    return default


def get_queue_items() -> list:
    queue_dir = BASE_PATH / "queue"
    items = []
    if queue_dir.exists():
        for f in sorted(queue_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            content = f.read_text()
            title = f.stem
            priority = "normal"
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    match = re.search(r'priority:\s*(\w+)', parts[1])
                    if match:
                        priority = match.group(1)
                    title_match = re.search(r'^#\s+(.+)$', parts[2], re.MULTILINE)
                    if title_match:
                        title = title_match.group(1)
            items.append({"title": title, "priority": priority})
    return items


def get_initiatives() -> list:
    content = read_file("goals/initiatives.md")
    initiatives = []
    in_active = False
    current = None
    for line in content.split('\n'):
        if '## Active Initiatives' in line:
            in_active = True
            continue
        if in_active and line.startswith('## ') and 'Active' not in line:
            break
        if in_active and line.startswith('### '):
            if current:
                initiatives.append(current)
            name = re.sub(r'^\d+\.\s*', '', line.replace('### ', '').strip())
            current = {"name": name, "status": "active"}
        if current and '**Status**:' in line:
            status = line.split('**Status**:')[1].strip().lower().split()[0]
            current["status"] = status
    if current:
        initiatives.append(current)
    return initiatives[:4]


def get_current_focus() -> str:
    content = read_file("memory/context.md")
    match = re.search(r'## Current Session Focus\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
    if match:
        return match.group(1).strip().split('\n')[0][:100]
    return "Autonomous operation"


def get_last_heartbeat_friendly() -> str:
    log_path = BASE_PATH / "logs" / "heartbeat.log"
    if log_path.exists():
        lines = log_path.read_text().strip().split('\n')
        for line in reversed(lines):
            if 'HEARTBEAT END' in line:
                return f"Last: {format_timestamp(line[:19] + 'Z')}"
    return "Active"


def get_evolution_entries() -> list:
    """Parse evolution log entries."""
    evo_path = BASE_PATH / "evolution" / "log.md"
    if not evo_path.exists():
        return []

    content = evo_path.read_text()
    entries = []

    # Split by ## headers (entries)
    parts = re.split(r'\n## ', content)
    for part in parts[1:]:  # Skip intro
        lines = part.strip().split('\n')
        if not lines:
            continue

        # Parse header line: "Title | Date"
        header = lines[0]
        title = header
        date = ""
        if ' | ' in header:
            title, date = header.split(' | ', 1)

        # Parse tags
        tags = []
        content_start = 1
        for i, line in enumerate(lines[1:], 1):
            if line.startswith('Tags:'):
                tags = [t.strip() for t in line.replace('Tags:', '').split(',')]
                content_start = i + 1
                break

        # Rest is content
        md_content = '\n'.join(lines[content_start:])
        if HAS_MARKDOWN:
            html_content = markdown.markdown(md_content)
        else:
            html_content = simple_markdown(md_content)

        entries.append({
            'title': title.strip(),
            'date': date.strip(),
            'tags': tags,
            'content': html_content
        })

    return entries


@app.route("/")
def index():
    queue = get_queue_items()
    return render_template(
        "index.html",
        metrics=fetch_moltbook_metrics(),
        activity=process_activity(read_all_activity()[:15]),
        activity_graph=get_activity_graph(),
        queue=queue,
        queue_count=len(queue),
        initiatives=get_initiatives(),
        current_focus=get_current_focus(),
        last_heartbeat_friendly=get_last_heartbeat_friendly(),
        last_refresh=datetime.now().strftime("%H:%M:%S")
    )


@app.route("/history")
def history():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    all_activity = read_all_activity()
    if status_filter:
        all_activity = [a for a in all_activity if a.get('status') == status_filter]
    total_count = len(all_activity)
    success_count = len([a for a in all_activity if a.get('status') == 'success'])
    failed_count = len([a for a in all_activity if a.get('status') == 'failed'])
    total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * ITEMS_PER_PAGE
    return render_template(
        "history.html",
        activity=process_activity(all_activity[start:start + ITEMS_PER_PAGE]),
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        success_count=success_count,
        failed_count=failed_count,
        filter_status=status_filter
    )


@app.route("/evolution")
def evolution():
    return render_template("evolution.html", entries=get_evolution_entries())


@app.route("/api/activity")
def api_activity():
    return jsonify(read_all_activity()[:100])


@app.route("/api/metrics")
def api_metrics():
    return jsonify(fetch_moltbook_metrics())


@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "metrics": fetch_moltbook_metrics()
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  Austnomaton Dashboard - http://localhost:8420")
    print("=" * 50)
    app.run(host="localhost", port=8420, debug=False)
