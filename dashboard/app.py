#!/usr/bin/env python3
"""
Austnomaton Dashboard
A lightweight Flask app for monitoring the austnomaton system.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Base path for austnomaton files
BASE_PATH = Path.home() / ".austnomaton"


def read_file(relative_path: str) -> str:
    """Read a file from the austnomaton directory."""
    file_path = BASE_PATH / relative_path
    if file_path.exists():
        return file_path.read_text()
    return ""


def read_jsonl(relative_path: str, limit: int = 50) -> list:
    """Read recent entries from a JSONL file."""
    file_path = BASE_PATH / relative_path
    if not file_path.exists():
        return []
    
    lines = file_path.read_text().strip().split("\n")
    entries = []
    for line in reversed(lines[-limit:]):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def parse_metrics() -> dict:
    """Parse metrics from metrics.md."""
    content = read_file("evolution/metrics.md")
    # Simple parsing - in production would be more robust
    metrics = {
        "moltbook_followers": 0,
        "x_followers": 0,
        "total_posts": 0,
        "revenue_mtd": 0,
    }
    
    # Could add actual parsing here
    return metrics


def get_context_summary() -> dict:
    """Get summary from context.md."""
    content = read_file("memory/context.md")
    return {
        "raw": content[:2000] if content else "No context available",
        "last_updated": "Unknown"
    }


def get_recent_posts(limit: int = 10) -> list:
    """Get recent posts from content-log.md."""
    content = read_file("memory/content-log.md")
    # Would parse actual posts in production
    return []


def get_active_tasks() -> list:
    """Get active tasks from active-tasks.md."""
    content = read_file("goals/active-tasks.md")
    tasks = []
    
    # Simple parsing for task headers
    in_task = False
    current_task = None
    
    for line in content.split("\n"):
        if line.startswith("### [ ]"):
            if current_task:
                tasks.append(current_task)
            current_task = {
                "title": line.replace("### [ ]", "").strip(),
                "status": "pending",
                "details": ""
            }
        elif line.startswith("### [x]") or line.startswith("### [X]"):
            if current_task:
                tasks.append(current_task)
            current_task = {
                "title": line.replace("### [x]", "").replace("### [X]", "").strip(),
                "status": "done",
                "details": ""
            }
        elif current_task and line.startswith("- "):
            current_task["details"] += line + "\n"
    
    if current_task:
        tasks.append(current_task)
    
    return tasks[:10]


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template(
        "index.html",
        metrics=parse_metrics(),
        context=get_context_summary(),
        activity=read_jsonl("logs/activity.jsonl", 20),
        tasks=get_active_tasks(),
        recent_posts=get_recent_posts(),
        last_refresh=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@app.route("/api/activity")
def api_activity():
    """API endpoint for activity log."""
    return jsonify(read_jsonl("logs/activity.jsonl", 50))


@app.route("/api/metrics")
def api_metrics():
    """API endpoint for metrics."""
    return jsonify(parse_metrics())


@app.route("/api/context")
def api_context():
    """API endpoint for context."""
    return jsonify(get_context_summary())


@app.route("/api/refresh")
def api_refresh():
    """Trigger a full refresh of dashboard data."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "metrics": parse_metrics(),
        "activity": read_jsonl("logs/activity.jsonl", 20),
        "context": get_context_summary()
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  Austnomaton Dashboard")
    print("  http://localhost:8420")
    print("=" * 50)
    app.run(host="localhost", port=8420, debug=True)
