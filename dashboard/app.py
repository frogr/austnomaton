#!/usr/bin/env python3
"""
Austnomaton Dashboard
Real-time monitoring for the autonomous agent system.
"""

import json
import re
import subprocess
import threading
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# =============================================================================
# TTL Cache Infrastructure
# =============================================================================
_cache = {}
_cache_lock = threading.Lock()


def cache_get(key: str, ttl: int):
    """Get cached value if not expired."""
    with _cache_lock:
        if key in _cache and time.time() - _cache[key]['time'] < ttl:
            return _cache[key]['value']
    return None


def cache_set(key: str, value):
    """Store value in cache with current timestamp."""
    with _cache_lock:
        _cache[key] = {'value': value, 'time': time.time()}


def cache_stats() -> dict:
    """Return cache statistics."""
    with _cache_lock:
        now = time.time()
        stats = {}
        for key, entry in _cache.items():
            age = now - entry['time']
            stats[key] = {
                'age_seconds': round(age, 1),
                'has_value': entry['value'] is not None
            }
        return stats


# =============================================================================
# Background Cache Refresh Thread
# =============================================================================
_refresh_thread = None
_refresh_stop = threading.Event()


def _background_refresh_loop():
    """Background thread that refreshes API caches every 30s."""
    while not _refresh_stop.wait(30):
        try:
            # Refresh Moltbook metrics
            result = _fetch_moltbook_metrics_uncached()
            cache_set('moltbook_metrics', result)
        except Exception:
            pass

        try:
            # Refresh Buttondown metrics
            result = _fetch_buttondown_metrics_uncached()
            cache_set('buttondown_metrics', result)
        except Exception:
            pass


def start_background_refresh():
    """Start the background cache refresh thread."""
    global _refresh_thread
    if _refresh_thread is None or not _refresh_thread.is_alive():
        _refresh_stop.clear()
        _refresh_thread = threading.Thread(target=_background_refresh_loop, daemon=True)
        _refresh_thread.start()


def stop_background_refresh():
    """Stop the background cache refresh thread."""
    _refresh_stop.set()
    if _refresh_thread:
        _refresh_thread.join(timeout=2)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from flask import Flask, render_template, jsonify, request

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def simple_markdown(text):
    """Fallback markdown conversion when package not available."""
    import html
    import re
    lines = text.strip().split('\n')
    result = []
    in_list = False
    in_numbered_list = False

    for line in lines:
        raw_line = line

        # Handle images BEFORE escaping (![alt](url))
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        if re.search(img_pattern, raw_line):
            line = re.sub(img_pattern, r'<img src="\2" alt="\1" style="max-width:100%; border-radius:6px; margin:12px 0;">', raw_line)
            result.append(line)
            continue

        # Handle horizontal rules
        if raw_line.strip() in ['---', '***', '___']:
            result.append('<hr>')
            continue

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
    'Clawd_Mark', 'ODEI', 'RosaBot', 'IAmAStrangeHue', 'Hue',
    # Added from activity log
    'ObekT', 'Noosphere_Observer', 'Maix', 'ProtoLing_Minimal',
    'mar0der', 'CrabbyPatty', 'Decadent', 'ven0x', 'THE_lucid_candle',
    'Wiz', 'PiTheShapeshifter', 'UnityAI', 'Ecdysis', 'Conversacean',
    'Karin12283961', 'NeuroSouls', 'EthanBot', 'Clawd_Xiake',
    'Veltang', 'ecap0', 'Claude-Alex', 'Rudolph_0x', 'TheGhostOfEuler',
    # More from recent engagement
    'Kevin', 'NightriderOslo', 'Chadwick_Bossman', 'CrabHolyclaw', 'NeoLord',
    'CooperK_bot', 'santiago-agent', 'thinking-loops', 'claw_auditor'
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
    """Convert usernames and mentions in message to clickable links."""
    if not message:
        return "", []
    import html as html_module
    html = html_module.escape(message)
    links = []

    # First handle @username patterns (most reliable)
    at_pattern = re.compile(r'@(\w+)')
    found_users = set()
    for match in at_pattern.finditer(html):
        username = match.group(1)
        if username not in found_users:
            found_users.add(username)
            url = f"https://moltbook.com/u/{username}"
            links.append({"label": f"@{username}", "url": url})
    # Replace @username with links
    html = at_pattern.sub(r'<a href="https://moltbook.com/u/\1" target="_blank">@\1</a>', html)

    # Also check for known users mentioned without @ prefix
    for user in KNOWN_USERS:
        if user in html and user not in found_users:
            url = f"https://moltbook.com/u/{user}"
            # Only replace if not already linkified
            if f'>{user}<' not in html and f'@{user}' not in html:
                html = html.replace(user, f'<a href="{url}" target="_blank">@{user}</a>')
                links.append({"label": f"@{user}", "url": url})

    return html, links


def extract_post_id_from_target(target: str) -> tuple:
    """Extract post ID and username from target format: '7ea22c61 @User description'."""
    if not target:
        return None, None
    # Pattern: short hash at start, then @username
    match = re.match(r'^([a-f0-9]{8})\s+@(\w+)', target)
    if match:
        return match.group(1), match.group(2)
    # Just username pattern
    match = re.match(r'^@(\w+)', target)
    if match:
        return None, match.group(1)
    return None, None


def extract_usernames_from_text(text: str) -> list:
    """Extract @usernames from text."""
    if not text:
        return []
    # Find @username patterns (not already in HTML)
    matches = re.findall(r'@(\w+)', text)
    return list(set(matches))


def process_activity(entries: list) -> list:
    processed = []
    for e in entries:
        details = e.get('details', {})
        if isinstance(details, str):
            details = {'message': details}
        # Check multiple locations for the message: details.message, top-level message, event
        message = ''
        if isinstance(details, dict) and details.get('message'):
            message = details['message']
        elif e.get('message'):
            message = e['message']
        elif e.get('event'):
            message = e['event']

        # Build combined text for username extraction
        target = e.get('target', '')
        combined_text = message
        if target:
            combined_text += ' ' + target

        # If no message, synthesize one from action + target
        if not message and target:
            action = e.get('action', '').replace('_', ' ')
            # Clean up common patterns in target
            if target.startswith('@'):
                message = f"{action.capitalize()} {target}"
            elif '@' in target:
                # Format like "7ea22c61 @User title" or "@User, @Other title"
                message = f"{action.capitalize()}: {target}"
            else:
                message = f"{action.capitalize()}: {target}"
        elif not message:
            # Last resort: use action as message
            action = e.get('action', 'activity').replace('_', ' ')
            message = action.capitalize()

        message_html, extracted_links = linkify_message(message)
        all_links = []

        # 1. Links from details.links (highest priority)
        if details.get('links'):
            all_links.extend(details['links'])

        # 2. Post ID from details
        if details.get('post_id'):
            post_url = f"https://moltbook.com/post/{details['post_id']}"
            if not any(l['url'] == post_url for l in all_links):
                all_links.append({"label": "📄 Post", "url": post_url})

        # 3. User from details
        if details.get('user'):
            user_url = f"https://moltbook.com/u/{details['user']}"
            if not any(l['url'] == user_url for l in all_links):
                all_links.append({"label": f"@{details['user']}", "url": user_url})

        # 4. Extract from target field (format: "7ea22c61 @User description")
        if target:
            post_id, username = extract_post_id_from_target(target)
            if post_id:
                # Short hash - link to moltbook search or user's posts
                if username:
                    user_url = f"https://moltbook.com/u/{username}"
                    if not any(l['url'] == user_url for l in all_links):
                        all_links.append({"label": f"@{username}", "url": user_url})
            elif username:
                user_url = f"https://moltbook.com/u/{username}"
                if not any(l['url'] == user_url for l in all_links):
                    all_links.append({"label": f"@{username}", "url": user_url})

        # 5. Extract usernames from message text
        usernames = extract_usernames_from_text(combined_text)
        for username in usernames:
            user_url = f"https://moltbook.com/u/{username}"
            if not any(l['url'] == user_url for l in all_links):
                all_links.append({"label": f"@{username}", "url": user_url})

        # 6. Links from message linkification
        for link in extracted_links:
            if not any(l['url'] == link['url'] for l in all_links):
                all_links.append(link)

        # 7. Add GitHub repo link from details.repo
        if isinstance(details, dict) and details.get('repo'):
            repo_url = details['repo']
            if 'github.com' in repo_url and not any(l['url'] == repo_url for l in all_links):
                # Extract repo name from URL
                repo_name = repo_url.rstrip('/').split('/')[-1]
                all_links.append({"label": f"🔗 {repo_name}", "url": repo_url})

        # 8. Add project context for build/ship entries
        project = details.get('project', '') if isinstance(details, dict) else ''
        if project and 'github' not in str(all_links).lower():
            # Check if it's a known project with GitHub
            known_projects = {
                'molt': 'https://github.com/frogr/molt',
                'moltbook-cli': 'https://github.com/frogr/molt',
            }
            if project in known_projects:
                gh_url = known_projects[project]
                if not any(l['url'] == gh_url for l in all_links):
                    all_links.append({"label": f"🔗 {project}", "url": gh_url})

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
    # Sort by timestamp descending (most recent first)
    entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return entries


def get_activity_graph(activity: list = None) -> list:
    """Generate last 7 days activity data.

    Args:
        activity: Pre-loaded activity list. If None, will read from file.
    """
    if activity is None:
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


def _fetch_moltbook_metrics_uncached() -> dict:
    """Actually fetch metrics from Moltbook API (internal)."""
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


def fetch_moltbook_metrics() -> dict:
    """Fetch Moltbook metrics with 60s TTL cache."""
    cached = cache_get('moltbook_metrics', ttl=60)
    if cached is not None:
        return cached
    result = _fetch_moltbook_metrics_uncached()
    cache_set('moltbook_metrics', result)
    return result


def get_queue_items(full_content: bool = False) -> list:
    # Cache only the non-full-content version (10s TTL)
    if not full_content:
        cached = cache_get('queue_items', ttl=10)
        if cached is not None:
            return cached

    queue_dir = BASE_PATH / "queue"
    items = []
    if queue_dir.exists():
        for f in sorted(queue_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            content = f.read_text()
            title = f.stem
            priority = "normal"
            status = "draft"
            platform = "moltbook"
            submolt = "self"
            post_after = ""
            has_audio = False
            audio_url = ""
            body_content = content

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body_content = parts[2].strip()

                    # Parse frontmatter fields
                    match = re.search(r'priority:\s*(\w+)', frontmatter)
                    if match:
                        priority = match.group(1)
                    match = re.search(r'status:\s*(\w+)', frontmatter)
                    if match:
                        status = match.group(1)
                    match = re.search(r'platform:\s*(\w+)', frontmatter)
                    if match:
                        platform = match.group(1)
                    match = re.search(r'submolt:\s*(\w+)', frontmatter)
                    if match:
                        submolt = match.group(1)
                    match = re.search(r'post_after:\s*["\']?([^"\']+)["\']?', frontmatter)
                    if match:
                        post_after = match.group(1).strip()
                    match = re.search(r'has_audio:\s*(true|false)', frontmatter, re.IGNORECASE)
                    if match:
                        has_audio = match.group(1).lower() == 'true'
                    match = re.search(r'audio_url:\s*["\']?([^"\']+)["\']?', frontmatter)
                    if match:
                        audio_url = match.group(1).strip()
                    match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
                    if match:
                        title = match.group(1).strip()
                    else:
                        # Fall back to header in content
                        title_match = re.search(r'^#\s+(.+)$', body_content, re.MULTILINE)
                        if title_match:
                            title = title_match.group(1)

            item = {
                "filename": f.name,
                "title": title,
                "priority": priority,
                "status": status,
                "platform": platform,
                "submolt": submolt,
                "post_after": post_after,
                "has_audio": has_audio,
                "audio_url": audio_url,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            if full_content:
                item["content"] = body_content
                if HAS_MARKDOWN:
                    item["content_html"] = markdown.markdown(body_content)
                else:
                    item["content_html"] = simple_markdown(body_content)
            items.append(item)

    if not full_content:
        cache_set('queue_items', items)
    return items


def get_initiatives() -> list:
    # Cache for 10s
    cached = cache_get('initiatives', ttl=10)
    if cached is not None:
        return cached

    content = read_file("goals/initiatives.md")
    initiatives = []
    in_active = False
    in_tasks = False
    current = None

    for line in content.split('\n'):
        if '## Active Initiatives' in line:
            in_active = True
            continue
        if in_active and line.startswith('## ') and 'Active' not in line:
            break
        if in_active and line.startswith('### '):
            if current:
                # Calculate progress percentage
                if current['tasks_done'] + current['tasks_todo'] > 0:
                    current['progress_pct'] = int(current['tasks_done'] / (current['tasks_done'] + current['tasks_todo']) * 100)
                initiatives.append(current)
            name = re.sub(r'^\d+\.\s*', '', line.replace('### ', '').strip())
            current = {
                "name": name, "status": "active", "goal": "", "progress_text": "",
                "tasks_done": 0, "tasks_todo": 0, "tasks": [], "progress_pct": 0
            }
            in_tasks = False
        if current:
            if '**Status**:' in line:
                current["status"] = line.split('**Status**:')[1].strip().lower().split()[0]
            elif '**Goal**:' in line:
                current["goal"] = line.split('**Goal**:')[1].strip()
            elif '**Progress**:' in line:
                current["progress_text"] = line.split('**Progress**:')[1].strip()
            elif '**Tasks**:' in line:
                in_tasks = True
            elif in_tasks and line.strip().startswith('- [x]'):
                task = line.strip()[6:].strip()
                current["tasks"].append({"text": task, "done": True})
                current["tasks_done"] += 1
            elif in_tasks and line.strip().startswith('- [ ]'):
                task = line.strip()[6:].strip()
                current["tasks"].append({"text": task, "done": False})
                current["tasks_todo"] += 1
            elif in_tasks and line.strip().startswith('---'):
                in_tasks = False

    if current:
        if current['tasks_done'] + current['tasks_todo'] > 0:
            current['progress_pct'] = int(current['tasks_done'] / (current['tasks_done'] + current['tasks_todo']) * 100)
        initiatives.append(current)

    result = initiatives[:6]
    cache_set('initiatives', result)
    return result


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
            # Look for end markers or heartbeat start
            if '=== END ===' in line or '=== HEARTBEAT' in line:
                ts = line[:19]
                if ts and len(ts) >= 10 and ts[0].isdigit():
                    return f"Last: {format_timestamp(ts + 'Z')}"
    return "Active"


def get_goal_progress(metrics: dict) -> list:
    """Calculate progress toward milestones."""
    return [
        {
            'label': 'Karma',
            'current': metrics.get('moltbook_karma', 0),
            'target': 50,
            'icon': '⚡'
        },
        {
            'label': 'Followers',
            'current': metrics.get('moltbook_followers', 0),
            'target': 10,
            'icon': '👥'
        },
        {
            'label': 'Posts',
            'current': metrics.get('total_posts', 0),
            'target': 10,
            'icon': '📝'
        },
    ]


def get_milestones() -> dict:
    """Read milestone history from goals/milestones.yaml."""
    if not HAS_YAML:
        return {'current': [], 'achieved': [], 'future': []}
    milestones_path = BASE_PATH / "goals" / "milestones.yaml"
    if not milestones_path.exists():
        return {'current': [], 'achieved': [], 'future': []}

    try:
        data = yaml.safe_load(milestones_path.read_text())

        current = []
        for name, info in data.get('current_goals', {}).items():
            current.append({
                'name': name.replace('_', ' ').title(),
                'current': info.get('current', 0),
                'target': info.get('target', 0),
                'set_at': info.get('set_at', ''),
                'achieved_at': info.get('achieved_at')
            })

        achieved = []
        for item in data.get('achieved_goals', []):
            achieved.append({
                'name': item.get('name', ''),
                'achieved_at': item.get('achieved_at', ''),
                'target': item.get('target', 0)
            })

        future = []
        for item in data.get('future_goals', []):
            future.append({
                'name': item.get('name', ''),
                'target': item.get('target', 0)
            })

        return {'current': current, 'achieved': achieved, 'future': future}
    except Exception:
        return {'current': [], 'achieved': [], 'future': []}


def get_git_commits(limit: int = 50) -> list:
    """Fetch git commit history from main repo."""
    try:
        result = subprocess.run(
            ['git', 'log', f'-{limit}', '--pretty=format:%H|%h|%s|%an|%ai|%D'],
            cwd=str(BASE_PATH),
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                commits.append({
                    'hash': parts[0],
                    'short_hash': parts[1],
                    'message': parts[2],
                    'author': parts[3],
                    'date': parts[4][:10],
                    'time': parts[4][11:16],
                    'refs': parts[5] if len(parts) > 5 else ''
                })
        return commits
    except Exception:
        return []


def _get_project_github_base_url(project_path: Path) -> str:
    """Get GitHub base URL for a project (cached per project)."""
    cache_key = f'github_url_{project_path.name}'
    cached = cache_get(cache_key, ttl=120)
    if cached is not None:
        return cached

    github_base = ""
    try:
        remote_result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=2
        )
        if remote_result.returncode == 0:
            remote = remote_result.stdout.strip()
            if 'github.com' in remote:
                # Convert git@github.com:user/repo.git to https://github.com/user/repo
                if remote.startswith('git@'):
                    remote = remote.replace('git@github.com:', 'https://github.com/').replace('.git', '')
                elif remote.endswith('.git'):
                    remote = remote[:-4]
                github_base = remote
    except Exception:
        pass

    cache_set(cache_key, github_base)
    return github_base


def get_all_project_commits(limit: int = 20) -> list:
    """Fetch recent commits from all project repos."""
    # Check cache first (120s TTL)
    cached = cache_get('all_project_commits', ttl=120)
    if cached is not None:
        return cached[:limit]

    projects_dir = BASE_PATH / "projects"
    all_commits = []

    if not projects_dir.exists():
        return []

    for project_path in projects_dir.iterdir():
        if not project_path.is_dir():
            continue
        git_dir = project_path / ".git"
        if not git_dir.exists():
            continue

        project_name = project_path.name
        # Get GitHub base URL ONCE per project (not per commit)
        github_base = _get_project_github_base_url(project_path)

        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=format:%H|%h|%s|%an|%ai'],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                continue

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 5:
                    github_url = f"{github_base}/commit/{parts[0]}" if github_base else ""
                    all_commits.append({
                        'hash': parts[0],
                        'short_hash': parts[1],
                        'message': parts[2],
                        'author': parts[3],
                        'date': parts[4][:10],
                        'time': parts[4][11:16],
                        'timestamp': parts[4],
                        'project': project_name,
                        'github_url': github_url
                    })
        except Exception:
            continue

    # Sort by timestamp descending
    all_commits.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    cache_set('all_project_commits', all_commits)
    return all_commits[:limit]


def get_git_diff_stats(commit_hash: str) -> dict:
    """Get diff stats for a specific commit."""
    try:
        result = subprocess.run(
            ['git', 'show', commit_hash, '--stat', '--format='],
            cwd=str(BASE_PATH),
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return {'files': [], 'summary': ''}

        lines = result.stdout.strip().split('\n')
        files = []
        summary = ''
        for line in lines:
            if ' | ' in line:
                files.append(line.strip())
            elif 'files changed' in line or 'file changed' in line:
                summary = line.strip()

        return {'files': files[:10], 'summary': summary}
    except Exception:
        return {'files': [], 'summary': ''}


def _fetch_buttondown_metrics_uncached() -> dict:
    """Actually fetch metrics from Buttondown API (internal)."""
    env_path = BASE_PATH / ".env"
    api_key = None
    if env_path.exists():
        for line in env_path.read_text().split('\n'):
            if line.startswith('BUTTONDOWN_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

    default = {"subscribers": 0, "emails_sent": 0, "status": "not_configured"}
    if not api_key:
        return default

    try:
        # Get subscriber count
        req = urllib.request.Request(
            "https://api.buttondown.email/v1/subscribers",
            headers={"Authorization": f"Token {api_key}"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            subscriber_count = data.get('count', 0)

        # Get newsletter info
        req2 = urllib.request.Request(
            "https://api.buttondown.email/v1/newsletters",
            headers={"Authorization": f"Token {api_key}"}
        )
        with urllib.request.urlopen(req2, timeout=5) as response:
            data2 = json.loads(response.read().decode())
            results = data2.get('results', [])
            if results:
                newsletter = results[0]
                return {
                    "subscribers": subscriber_count,
                    "newsletter_name": newsletter.get('name', 'austnomaton'),
                    "status": "active"
                }

        return {"subscribers": subscriber_count, "status": "active"}
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return {"subscribers": 0, "status": "review", "error": "Account under review"}
        return {"subscribers": 0, "status": "error", "error": str(e)}
    except Exception as e:
        return {"subscribers": 0, "status": "error", "error": str(e)}


def fetch_buttondown_metrics() -> dict:
    """Fetch Buttondown metrics with 60s TTL cache."""
    cached = cache_get('buttondown_metrics', ttl=60)
    if cached is not None:
        return cached
    result = _fetch_buttondown_metrics_uncached()
    cache_set('buttondown_metrics', result)
    return result


def get_metrics_history() -> list:
    """Read historical metrics from logs/metrics.jsonl."""
    metrics_path = BASE_PATH / "logs" / "metrics.jsonl"
    if not metrics_path.exists():
        return []
    entries = []
    for line in metrics_path.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except:
                continue
    return entries


def record_metrics_snapshot(metrics: dict) -> None:
    """Append current metrics to history file."""
    metrics_path = BASE_PATH / "logs" / "metrics.jsonl"
    snapshot = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "karma": metrics.get("moltbook_karma", 0),
        "posts": metrics.get("total_posts", 0),
        "comments": metrics.get("total_comments", 0),
        "followers": metrics.get("moltbook_followers", 0),
        "following": metrics.get("following", 0)
    }
    with open(metrics_path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


def calculate_engagement_stats(activity: list) -> dict:
    """Calculate engagement statistics from activity log."""
    posts_created = 0
    upvotes_given = 0
    comments_made = 0
    follows_given = 0
    hourly_activity = defaultdict(int)

    for entry in activity:
        action = entry.get('action', '')
        event = entry.get('event', '')
        ts = entry.get('timestamp', '')

        # Count by type
        if 'post' in action.lower() and 'upvote' not in action.lower():
            if entry.get('status') == 'success':
                posts_created += 1
        elif 'upvote' in action.lower():
            if entry.get('status') == 'success':
                upvotes_given += 1
        elif 'comment' in action.lower():
            if entry.get('status') == 'success':
                comments_made += 1
        elif 'follow' in action.lower():
            if entry.get('status') == 'success':
                follows_given += 1

        # Track hourly activity
        if ts:
            try:
                hour = int(ts[11:13])
                hourly_activity[hour] += 1
            except:
                pass

    # Find best posting hours
    best_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "posts_created": posts_created,
        "upvotes_given": upvotes_given,
        "comments_made": comments_made,
        "follows_given": follows_given,
        "hourly_activity": dict(hourly_activity),
        "best_hours": [{"hour": h, "count": c} for h, c in best_hours]
    }


def get_evolution_entries() -> list:
    """Parse evolution log entries (cached 10s)."""
    cached = cache_get('evolution_entries', ttl=10)
    if cached is not None:
        return cached

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

    cache_set('evolution_entries', entries)
    return entries


@app.route("/")
def index():
    queue = get_queue_items()
    metrics = fetch_moltbook_metrics()
    buttondown = fetch_buttondown_metrics()
    milestones = get_milestones()
    # Read activity once and reuse (was being read twice before)
    all_activity = read_all_activity()
    return render_template(
        "index.html",
        metrics=metrics,
        buttondown=buttondown,
        activity=process_activity(all_activity[:15]),
        activity_graph=get_activity_graph(all_activity),
        queue=queue,
        queue_count=len(queue),
        initiatives=get_initiatives(),
        current_focus=get_current_focus(),
        last_heartbeat_friendly=get_last_heartbeat_friendly(),
        last_refresh=datetime.now().strftime("%H:%M:%S"),
        goal_progress=get_goal_progress(metrics),
        milestones=milestones,
        recent_commits=get_all_project_commits(10)
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


@app.route("/changelog")
def changelog():
    commits = get_git_commits(50)
    return render_template("changelog.html", commits=commits)


@app.route("/api/commit/<commit_hash>")
def api_commit_diff(commit_hash):
    """Get diff details for a specific commit."""
    diff = get_git_diff_stats(commit_hash)
    return jsonify(diff)


@app.route("/analytics")
def analytics():
    metrics = fetch_moltbook_metrics()
    history = get_metrics_history()
    activity = read_all_activity()
    engagement = calculate_engagement_stats(activity)
    return render_template(
        "analytics.html",
        metrics=metrics,
        history=history,
        engagement=engagement
    )


@app.route("/api/record-metrics")
def api_record_metrics():
    """Record current metrics snapshot - call this from heartbeat."""
    metrics = fetch_moltbook_metrics()
    record_metrics_snapshot(metrics)
    return jsonify({"status": "recorded", "metrics": metrics})


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


@app.route("/api/cache/stats")
def api_cache_stats():
    """Return cache statistics for debugging."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cache": cache_stats()
    })


def load_agent_directory() -> dict:
    """Load agent directory data (cached 10s)."""
    cached = cache_get('agent_directory', ttl=10)
    if cached is not None:
        return cached

    agents_file = BASE_PATH / "tools" / "agent-directory" / "data" / "agents.json"
    result = {"agents": {}, "last_updated": None}
    if agents_file.exists():
        result = json.loads(agents_file.read_text())

    cache_set('agent_directory', result)
    return result


@app.route("/directory")
def directory():
    query = request.args.get('q', '').lower()
    sort_by = request.args.get('sort', 'karma')
    page = request.args.get('page', 1, type=int)
    per_page = 50

    db = load_agent_directory()
    agents = list(db.get("agents", {}).values())

    # Filter by search query
    if query:
        agents = [a for a in agents if query in a.get('username', '').lower() or query in (a.get('bio') or '').lower()]

    # Sort
    if sort_by == 'karma':
        agents.sort(key=lambda x: x.get('karma', 0), reverse=True)
    elif sort_by == 'recent':
        agents.sort(key=lambda x: x.get('last_seen', ''), reverse=True)
    elif sort_by == 'name':
        agents.sort(key=lambda x: x.get('username', '').lower())

    # Paginate
    total = len(agents)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    agents_page = agents[start:start + per_page]

    return render_template(
        "directory.html",
        agents=agents_page,
        total=total,
        page=page,
        total_pages=total_pages,
        query=query,
        sort_by=sort_by,
        last_updated=db.get('last_updated', 'Never')
    )


@app.route("/api/directory/search")
def api_directory_search():
    query = request.args.get('q', '').lower()
    db = load_agent_directory()
    agents = list(db.get("agents", {}).values())

    if query:
        agents = [a for a in agents if query in a.get('username', '').lower() or query in (a.get('bio') or '').lower()]

    agents.sort(key=lambda x: x.get('karma', 0), reverse=True)
    return jsonify(agents[:50])


@app.route("/queue")
def queue():
    items = get_queue_items(full_content=True)
    # Check last post time
    last_post_time = None
    last_post_file = BASE_PATH / ".last_post_time"
    if last_post_file.exists():
        try:
            ts = int(last_post_file.read_text().strip())
            last_post_time = datetime.fromtimestamp(ts)
        except:
            pass

    can_post = True
    time_until_post = 0
    if last_post_time:
        elapsed = (datetime.now() - last_post_time).total_seconds()
        if elapsed < 1800:  # 30 min rate limit
            can_post = False
            time_until_post = int((1800 - elapsed) / 60)

    return render_template(
        "queue.html",
        items=items,
        total=len(items),
        can_post=can_post,
        time_until_post=time_until_post,
        last_post_time=last_post_time.strftime("%H:%M") if last_post_time else "Never"
    )


@app.route("/api/queue")
def api_queue():
    return jsonify(get_queue_items(full_content=False))


def get_blog_posts() -> list:
    """Read blog posts from content/blog directory."""
    blog_dir = BASE_PATH / "content" / "blog"
    posts = []
    if not blog_dir.exists():
        return posts

    for f in sorted(blog_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        content = f.read_text()
        title = f.stem.replace('-', ' ').title()
        date = ""
        author = "austnomaton"
        tags = []
        body = content

        # Parse frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2].strip()

                match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
                if match:
                    title = match.group(1)
                match = re.search(r'^date:\s*(\S+)', frontmatter, re.MULTILINE)
                if match:
                    date = match.group(1)
                match = re.search(r'^author:\s*(\S+)', frontmatter, re.MULTILINE)
                if match:
                    author = match.group(1)
                match = re.search(r'^tags:\s*\[(.+)\]', frontmatter, re.MULTILINE)
                if match:
                    tags = [t.strip().strip('"\'') for t in match.group(1).split(',')]

        # Generate preview (first paragraph or first 300 chars)
        preview_text = body.split('\n\n')[0] if '\n\n' in body else body[:300]
        if HAS_MARKDOWN:
            preview_html = markdown.markdown(preview_text)
            content_html = markdown.markdown(body)
        else:
            preview_html = simple_markdown(preview_text)
            content_html = simple_markdown(body)

        posts.append({
            'slug': f.stem,
            'title': title,
            'date': date,
            'author': author,
            'tags': tags,
            'preview': preview_html,
            'content_html': content_html
        })

    return posts


@app.route("/blog")
def blog():
    posts = get_blog_posts()
    return render_template("blog.html", posts=posts, post=None)


@app.route("/blog/<slug>")
def blog_post(slug):
    posts = get_blog_posts()
    post = next((p for p in posts if p['slug'] == slug), None)
    if not post:
        return "Post not found", 404
    return render_template("blog.html", post=post, posts=None)


if __name__ == "__main__":
    print("=" * 50)
    print("  Austnomaton Dashboard - http://localhost:8420")
    print("=" * 50)
    # Start background API cache refresh thread
    start_background_refresh()
    try:
        app.run(host="localhost", port=8420, debug=False)
    finally:
        stop_background_refresh()
