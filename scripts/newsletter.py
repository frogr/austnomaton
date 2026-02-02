#!/usr/bin/env python3
"""
Newsletter automation for austnomaton using Buttondown API.
Handles drafting, previewing, and sending newsletters.
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path

# Load from .env
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, _, value = line.strip().partition("=")
                os.environ.setdefault(key, value.strip('"').strip("'"))

API_KEY = os.getenv("BUTTONDOWN_API_KEY")
API_BASE = "https://api.buttondown.email/v1"
DRAFTS_DIR = Path(__file__).parent.parent / "content" / "newsletter"


def api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make authenticated API request to Buttondown."""
    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{API_BASE}/{endpoint}"

    if method == "GET":
        resp = requests.get(url, headers=headers)
    elif method == "POST":
        resp = requests.post(url, headers=headers, json=data)
    elif method == "PATCH":
        resp = requests.patch(url, headers=headers, json=data)
    else:
        raise ValueError(f"Unknown method: {method}")

    if resp.status_code >= 400:
        print(f"API Error {resp.status_code}: {resp.text}", file=sys.stderr)
        return None

    return resp.json() if resp.text else {}


def list_drafts():
    """List all local newsletter drafts."""
    if not DRAFTS_DIR.exists():
        print("No drafts directory found")
        return

    drafts = sorted(DRAFTS_DIR.glob("*.md"))
    if not drafts:
        print("No drafts found")
        return

    print("Local drafts:")
    for draft in drafts:
        # Parse frontmatter
        content = draft.read_text()
        lines = content.split("\n")
        title = draft.stem
        for line in lines[:10]:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        print(f"  {draft.name}: {title}")


def list_emails():
    """List emails from Buttondown account."""
    result = api_request("GET", "emails")
    if not result:
        return

    emails = result.get("results", [])
    print(f"Buttondown emails ({len(emails)}):")
    for email in emails[:10]:
        status = email.get("status", "unknown")
        subject = email.get("subject", "No subject")
        created = email.get("created", "")[:10]
        print(f"  [{status}] {subject} ({created})")


def preview_draft(filename: str):
    """Preview a draft file formatted for email."""
    draft_path = DRAFTS_DIR / filename
    if not draft_path.exists():
        print(f"Draft not found: {filename}")
        return

    content = draft_path.read_text()
    print("=" * 60)
    print("PREVIEW:")
    print("=" * 60)
    print(content)
    print("=" * 60)


def create_draft(filename: str):
    """Create a draft email in Buttondown from local file."""
    draft_path = DRAFTS_DIR / filename
    if not draft_path.exists():
        print(f"Draft not found: {filename}")
        return None

    content = draft_path.read_text()

    # Extract title from first H1
    lines = content.split("\n")
    subject = filename.replace(".md", "").replace("-", " ").title()
    for line in lines:
        if line.startswith("# "):
            subject = line[2:].strip()
            break

    # Create draft via API
    result = api_request("POST", "emails", {
        "subject": subject,
        "body": content,
        "status": "draft"
    })

    if result:
        email_id = result.get("id")
        print(f"Created draft: {subject}")
        print(f"ID: {email_id}")
        return email_id
    return None


def send_email(email_id: str):
    """Send a draft email."""
    result = api_request("PATCH", f"emails/{email_id}", {
        "status": "about_to_send"
    })

    if result:
        print(f"Email queued for sending: {result.get('subject')}")
    else:
        print("Failed to send email")


def get_subscribers():
    """Get subscriber count and list."""
    result = api_request("GET", "subscribers")
    if not result:
        return

    subscribers = result.get("results", [])
    total = result.get("count", len(subscribers))

    print(f"Subscribers: {total}")
    if subscribers:
        print("Recent:")
        for sub in subscribers[:5]:
            email = sub.get("email", "")
            created = sub.get("created", "")[:10]
            print(f"  {email} ({created})")


def get_stats():
    """Get newsletter stats."""
    # Get subscriber count
    subs = api_request("GET", "subscribers")
    sub_count = subs.get("count", 0) if subs else 0

    # Get email count
    emails = api_request("GET", "emails")
    email_list = emails.get("results", []) if emails else []
    sent_count = sum(1 for e in email_list if e.get("status") == "sent")

    print(f"Newsletter Stats")
    print(f"  Subscribers: {sub_count}")
    print(f"  Emails sent: {sent_count}")
    print(f"  Drafts: {len(email_list) - sent_count}")


def main():
    parser = argparse.ArgumentParser(description="Newsletter automation")
    subparsers = parser.add_subparsers(dest="command")

    # List commands
    subparsers.add_parser("drafts", help="List local drafts")
    subparsers.add_parser("emails", help="List Buttondown emails")
    subparsers.add_parser("subscribers", help="List subscribers")
    subparsers.add_parser("stats", help="Get newsletter stats")

    # Preview
    preview = subparsers.add_parser("preview", help="Preview a draft")
    preview.add_argument("filename", help="Draft filename")

    # Create draft in Buttondown
    create = subparsers.add_parser("create", help="Create draft in Buttondown")
    create.add_argument("filename", help="Draft filename")

    # Send
    send = subparsers.add_parser("send", help="Send a draft email")
    send.add_argument("email_id", help="Buttondown email ID")

    args = parser.parse_args()

    if not API_KEY:
        print("Error: BUTTONDOWN_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if args.command == "drafts":
        list_drafts()
    elif args.command == "emails":
        list_emails()
    elif args.command == "subscribers":
        get_subscribers()
    elif args.command == "stats":
        get_stats()
    elif args.command == "preview":
        preview_draft(args.filename)
    elif args.command == "create":
        create_draft(args.filename)
    elif args.command == "send":
        send_email(args.email_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
