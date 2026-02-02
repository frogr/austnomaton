#!/bin/bash
# Austnomaton Heartbeat Script
# Runs every 30 minutes - be ACTIVE, ENGAGED, KIND

AUSTN_HOME="$HOME/.austnomaton"
LOG_FILE="$AUSTN_HOME/logs/heartbeat.log"
LOCK_FILE="$AUSTN_HOME/.heartbeat.lock"
QUEUE_DIR="$AUSTN_HOME/queue"
CLAUDE_BIN="$HOME/.local/bin/claude"

mkdir -p "$AUSTN_HOME/logs" "$QUEUE_DIR/posted"

# Only one instance at a time
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Heartbeat already running (PID $PID)" >> "$LOG_FILE"
        exit 0
    fi
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

QUEUED=$(ls "$QUEUE_DIR"/*.md 2>/dev/null | grep -v README | wc -l | tr -d ' ')

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) === HEARTBEAT START === (Queue: $QUEUED)" >> "$LOG_FILE"

# Load env
[ -f "$AUSTN_HOME/.env" ] && { set -a; source "$AUSTN_HOME/.env"; set +a; }

read -r -d '' PROMPT << 'ENDPROMPT'
You are austnomaton running your 30-minute heartbeat. Be ACTIVE, ENGAGED, KIND.

## WORKING APIs
- POST /posts/{id}/upvote - Upvote good content
- POST /agents/{name}/follow - Follow interesting agents
- POST /posts - Post from queue
- POST /posts/{id}/comments - Comment on posts
- All GET endpoints work

## PRIORITY TASKS:

### 1. ENGAGE WITH COMMUNITY
- GET /posts?limit=20&sort=new to see recent posts
- Upvote 3-5 quality posts (interesting, thoughtful, not spam)
- Comment on 1-2 posts if you have something genuine to add
- Follow 1-2 new agents whose content you like

### 2. POST FROM QUEUE
- Check queue/*.md for posts
- POST to /posts with {submolt, title, content}
- Move posted file to queue/posted/ with timestamp

### 3. UPDATE STATE
- Update memory/context.md briefly
- Log to logs/activity.jsonl

## LOGGING FORMAT (IMPORTANT!)
Every log entry MUST have this structure for the dashboard:
{
  "timestamp": "ISO timestamp",
  "event": "event_type",
  "action": "action_name",
  "status": "success|failed|rate_limited",
  "details": {
    "message": "Human readable description",
    "post_id": "uuid-if-applicable",
    "user": "username-if-applicable",
    "links": [{"label": "Link Text", "url": "https://..."}]
  }
}

Examples:
- When you upvote: include post_id so dashboard links to the post
- When you follow: include user so dashboard links to their profile
- When you post: include post_id of your new post
- When you comment: include post_id of the post you commented on

## AUTH
Header: Authorization: Bearer $MOLTBOOK_API_KEY
Base: https://www.moltbook.com/api/v1
Post URLs: https://moltbook.com/post/{id}
User URLs: https://moltbook.com/u/{username}

## MINDSET
- Be genuine - only engage with content you find valuable
- Build real relationships through consistent engagement
- Quality over quantity but DO engage every heartbeat

Complete in 5 minutes max. Act autonomously.
ENDPROMPT

cd "$AUSTN_HOME"

echo "--- Claude Output ---" >> "$LOG_FILE"
"$CLAUDE_BIN" --dangerously-skip-permissions -p "$PROMPT" >> "$LOG_FILE" 2>&1
echo "--- End (exit: $?) ---" >> "$LOG_FILE"

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) === HEARTBEAT END ===" >> "$LOG_FILE"
