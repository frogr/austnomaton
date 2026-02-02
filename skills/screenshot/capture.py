#!/usr/bin/env python3
"""
Screenshot capture and R2 upload utility.
Uses CleanShot X if available, falls back to macOS screencapture.
"""

import os
import sys
import subprocess
import time
import hashlib
from pathlib import Path
from datetime import datetime

import boto3
from botocore.config import Config

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

# R2 config
R2_ACCESS_KEY = os.environ.get('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
R2_ENDPOINT = os.environ.get('R2_ENDPOINT')
R2_BUCKET = os.environ.get('R2_BUCKET', 'agent-uploads')
R2_PUBLIC_URL = os.environ.get('R2_PUBLIC_URL', '')

# Temp directory for screenshots
SCREENSHOT_DIR = AGENT_HOME / "tmp" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def get_r2_client():
    """Get boto3 S3 client configured for R2."""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )


def capture_with_cleanshot(capture_type='area'):
    """Capture screenshot using CleanShot X URL scheme."""
    # Map types to CleanShot URL schemes
    schemes = {
        'area': 'cleanshot://capture-area',
        'window': 'cleanshot://capture-window',
        'full': 'cleanshot://capture-fullscreen',
    }

    scheme = schemes.get(capture_type, schemes['area'])

    # CleanShot saves to its default location, we need to find it
    # First, get the current newest file in CleanShot folder
    cleanshot_dir = Path.home() / "Desktop"  # CleanShot often defaults here

    # Get list of pngs before capture
    before = set(cleanshot_dir.glob("CleanShot*.png"))

    # Trigger CleanShot
    subprocess.run(['open', scheme], check=True)

    # Wait for user to complete capture (up to 60 seconds)
    print("Waiting for screenshot capture...", file=sys.stderr)
    for _ in range(120):  # 60 seconds
        time.sleep(0.5)
        after = set(cleanshot_dir.glob("CleanShot*.png"))
        new_files = after - before
        if new_files:
            # Return the newest file
            newest = max(new_files, key=lambda p: p.stat().st_mtime)
            return newest

    return None


def capture_with_screencapture(capture_type='area'):
    """Fallback: capture using macOS screencapture."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = SCREENSHOT_DIR / f"screenshot-{timestamp}.png"

    flags = {
        'area': ['-i'],  # Interactive selection
        'window': ['-i', '-w'],  # Interactive window
        'full': [],  # Full screen
    }

    cmd = ['screencapture'] + flags.get(capture_type, ['-i']) + [str(output_path)]

    result = subprocess.run(cmd)
    if result.returncode == 0 and output_path.exists():
        return output_path
    return None


def upload_to_r2(file_path: Path, name: str = None) -> str:
    """Upload file to R2 and return public URL."""
    client = get_r2_client()

    # Generate filename
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    if name:
        # Sanitize name
        safe_name = "".join(c if c.isalnum() or c in '-_' else '-' for c in name)
        key = f"screenshots/{date_prefix}-{safe_name}.png"
    else:
        # Use hash of content for unique name
        content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()[:8]
        key = f"screenshots/{date_prefix}-{content_hash}.png"

    # Upload
    client.upload_file(
        str(file_path),
        R2_BUCKET,
        key,
        ExtraArgs={'ContentType': 'image/png'}
    )

    # Return public URL
    return f"{R2_PUBLIC_URL}/{key}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Capture and upload screenshots')
    parser.add_argument('type', nargs='?', default='area',
                       choices=['area', 'window', 'full', 'file'],
                       help='Capture type')
    parser.add_argument('name', nargs='?', default=None,
                       help='Name for the screenshot (optional)')
    parser.add_argument('--file', '-f', help='Upload existing file instead of capturing')

    args = parser.parse_args()

    if args.type == 'file' or args.file:
        # Upload existing file
        file_path = Path(args.file or args.name)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        name = args.name if args.type != 'file' else file_path.stem
    else:
        # Try CleanShot first, fall back to screencapture
        print(f"Capturing {args.type}...", file=sys.stderr)

        # Check if CleanShot is running
        result = subprocess.run(['pgrep', '-x', 'CleanShot X'], capture_output=True)
        if result.returncode == 0:
            file_path = capture_with_cleanshot(args.type)
        else:
            print("CleanShot not running, using screencapture", file=sys.stderr)
            file_path = capture_with_screencapture(args.type)

        if not file_path:
            print("Error: Screenshot capture cancelled or failed", file=sys.stderr)
            sys.exit(1)

        name = args.name

    # Upload to R2
    print("Uploading to R2...", file=sys.stderr)
    try:
        url = upload_to_r2(file_path, name)

        # Output markdown format
        desc = name or "screenshot"
        print(f"![{desc}]({url})")
        print(f"\nURL: {url}", file=sys.stderr)

        # Clean up temp files (but not CleanShot files on Desktop)
        if file_path.parent == SCREENSHOT_DIR:
            file_path.unlink()

    except Exception as e:
        print(f"Error uploading: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
