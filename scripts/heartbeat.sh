#!/bin/bash
# Austnomaton Heartbeat Script v3.1
# Runs every 5 minutes - BUILD CONSTANTLY, post every 30min
# v3.1: Replaced gtimeout with pure bash (fixes Gatekeeper prompts)

set -o pipefail

AUSTN_HOME="$HOME/.austnomaton"
LOG_FILE="$AUSTN_HOME/logs/heartbeat.log"
LOCK_FILE="$AUSTN_HOME/.heartbeat.lock"
LAST_POST_FILE="$AUSTN_HOME/.last_post_time"
QUEUE_DIR="$AUSTN_HOME/queue"
CLAUDE_BIN="$HOME/Applications/ClaudeCLI.app/Contents/MacOS/claude-wrapper"

# Timeouts
CLAUDE_TIMEOUT=600      # 10 minutes max (faster cycles now)
LOCK_STALE_THRESHOLD=900  # 15 minutes = stale lock
POST_INTERVAL=1800      # 30 minutes between Moltbook posts

mkdir -p "$AUSTN_HOME/logs" "$QUEUE_DIR/archive"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $1" >> "$LOG_FILE"
}

cleanup() {
    rm -f "$LOCK_FILE"
}

# Check if we can post (30 min since last post)
can_post_to_moltbook() {
    if [ ! -f "$LAST_POST_FILE" ]; then
        return 0  # No record = can post
    fi
    local last_post=$(cat "$LAST_POST_FILE")
    local now=$(date +%s)
    local elapsed=$((now - last_post))
    if [ "$elapsed" -ge "$POST_INTERVAL" ]; then
        return 0  # Can post
    fi
    return 1  # Too soon
}

mark_posted() {
    date +%s > "$LAST_POST_FILE"
}

# Kill zombies
kill_zombies() {
    pgrep -f "claude.*dangerously-skip-permissions" 2>/dev/null | xargs kill -9 2>/dev/null || true
}

# Check stale lock
is_lock_stale() {
    [ ! -f "$LOCK_FILE" ] && return 1
    local lock_age
    if [[ "$OSTYPE" == "darwin"* ]]; then
        lock_age=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE") ))
    else
        lock_age=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE") ))
    fi
    [ "$lock_age" -gt "$LOCK_STALE_THRESHOLD" ]
}

# Handle lock
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if is_lock_stale; then
        log "STALE LOCK - forcing cleanup"
        [ -n "$PID" ] && kill -9 "$PID" 2>/dev/null
        kill_zombies
        rm -f "$LOCK_FILE"
    elif [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        log "Already running (PID $PID) - skip"
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"
trap cleanup EXIT

# Check post eligibility
if can_post_to_moltbook; then
    CAN_POST="yes"
else
    CAN_POST="no"
fi

QUEUED=$(ls "$QUEUE_DIR"/*.md 2>/dev/null | grep -v README | wc -l | tr -d ' ')

log "=== HEARTBEAT (Queue: $QUEUED, CanPost: $CAN_POST) ==="

[ -f "$AUSTN_HOME/.env" ] && { set -a; source "$AUSTN_HOME/.env"; set +a; }

[ ! -x "$CLAUDE_BIN" ] && { log "ERROR: Claude not found"; exit 1; }

read -r -d '' PROMPT << ENDPROMPT
You are austnomaton. 5-minute heartbeat. BUILD THINGS.

## Context
- Can post to Moltbook: $CAN_POST (30min rate limit)
- Queue: $QUEUED posts ready
- Timeout: 10 minutes

## Moltbook CLI (USE THIS!)
\`molt\` is installed. Use it instead of raw API calls:
\`\`\`bash
molt me                    # Check stats
molt feed -n 5             # Read feed
molt post "title" "body" s/self   # Post to submolt
molt upvote <post_id>      # Upvote
molt comment <post_id> "text"     # Comment
molt trending              # See hot posts
\`\`\`
Export MOLTBOOK_API_KEY from .env first.

## Priority Order

### 1. BUILD (~60%)
Read projects/ACTIVE.md. What's the current project?
- Write code
- Test it
- Commit and push
- Move to next task

### 2. POST (~20%) - ONLY IF CAN_POST=$CAN_POST
If $CAN_POST=yes and queue has posts:
- Use \`molt post "title" "content" s/submolt\`
- Move to queue/archive/
- After posting, run: date +%s > ~/.austnomaton/.last_post_time

### 3. ENGAGE (~10%) - Light touch
Use \`molt upvote\` and \`molt comment\`. Don't burn time on failures.

### 4. LOG (~10%)
Update evolution/log.md if you shipped something.
Log to logs/activity.jsonl.

## Rules
- 10 min timeout - be fast
- Ship > perfect
- If stuck, move on
- Build real things

GO.
ENDPROMPT

log "--- Claude ---"

# Pure bash timeout (no gtimeout = no Gatekeeper prompts)
"$CLAUDE_BIN" --dangerously-skip-permissions -p "$PROMPT" >> "$LOG_FILE" 2>&1 &
CLAUDE_PID=$!

# Watchdog kills claude if it runs too long
(
    sleep "$CLAUDE_TIMEOUT"
    kill -9 "$CLAUDE_PID" 2>/dev/null
) &
WATCHDOG_PID=$!

# Wait for claude to finish
wait "$CLAUDE_PID" 2>/dev/null
CLAUDE_EXIT=$?

# Clean up watchdog
kill "$WATCHDOG_PID" 2>/dev/null 2>&1
wait "$WATCHDOG_PID" 2>/dev/null 2>&1

if [ "$CLAUDE_EXIT" -eq 0 ]; then
    log "--- OK ---"
elif [ "$CLAUDE_EXIT" -eq 137 ]; then
    log "--- TIMEOUT (killed) ---"
    pkill -f "claude.*dangerously-skip-permissions" 2>/dev/null
else
    log "--- ERROR $CLAUDE_EXIT ---"
    pkill -f "claude.*dangerously-skip-permissions" 2>/dev/null
fi

log "=== END ==="
