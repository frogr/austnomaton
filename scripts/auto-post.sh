#!/bin/bash
# Auto-post from queue to Moltbook
# Usage: ./auto-post.sh
# Checks rate limit, posts oldest ready item, archives it

set -e

AUSTN_HOME="${AUSTN_HOME:-$HOME/.austnomaton}"
QUEUE_DIR="$AUSTN_HOME/queue"
ARCHIVE_DIR="$QUEUE_DIR/archive"
POSTED_DIR="$QUEUE_DIR/posted"
LAST_POST_FILE="$AUSTN_HOME/.last_post_time"
POST_INTERVAL=1800  # 30 minutes

source "$AUSTN_HOME/.env" 2>/dev/null || true

# Check rate limit
can_post() {
    [ ! -f "$LAST_POST_FILE" ] && return 0
    local last=$(cat "$LAST_POST_FILE")
    local now=$(date +%s)
    local elapsed=$((now - last))
    [ "$elapsed" -ge "$POST_INTERVAL" ]
}

# Parse frontmatter from queue file
parse_frontmatter() {
    local file="$1"
    local key="$2"
    sed -n '/^---$/,/^---$/p' "$file" | grep "^${key}:" | head -1 | sed "s/^${key}:[[:space:]]*//" | tr -d '"'
}

# Extract body (everything after frontmatter)
get_body() {
    local file="$1"
    awk '/^---$/{if(++n==2){f=1;next}}f' "$file" | sed '/^$/d' | head -1
}

# Get full content (for posts that need it)
get_full_content() {
    local file="$1"
    awk '/^---$/{if(++n==2){f=1;next}}f' "$file"
}

# Find oldest ready queue item
find_ready_post() {
    for f in "$QUEUE_DIR"/*.md; do
        [ ! -f "$f" ] && continue
        [ "$(basename "$f")" = "README.md" ] && continue
        local status=$(parse_frontmatter "$f" "status")
        [ "$status" = "ready" ] && echo "$f" && return 0
    done
    return 1
}

main() {
    mkdir -p "$ARCHIVE_DIR" "$POSTED_DIR"

    # Check rate limit
    if ! can_post; then
        local last=$(cat "$LAST_POST_FILE")
        local now=$(date +%s)
        local wait=$((POST_INTERVAL - (now - last)))
        echo "Rate limited. Wait ${wait}s"
        exit 1
    fi

    # Find a post
    local post_file
    post_file=$(find_ready_post) || { echo "No ready posts in queue"; exit 0; }

    echo "Found: $post_file"

    # Parse metadata
    local title=$(parse_frontmatter "$post_file" "title")
    local submolt=$(parse_frontmatter "$post_file" "submolt")
    local content=$(get_full_content "$post_file")

    [ -z "$title" ] && { echo "ERROR: No title in $post_file"; exit 1; }
    [ -z "$submolt" ] && submolt="self"

    echo "Title: $title"
    echo "Submolt: s/$submolt"
    echo "Content preview: ${content:0:100}..."
    echo ""

    # Post using molt
    echo "Posting..."
    if molt post "$title" "$content" "s/$submolt"; then
        echo "SUCCESS!"

        # Update rate limit tracker
        date +%s > "$LAST_POST_FILE"

        # Archive the post
        local timestamp=$(date +%Y%m%d-%H%M%S)
        local basename=$(basename "$post_file" .md)
        mv "$post_file" "$POSTED_DIR/${basename}-${timestamp}.md"
        echo "Archived to: $POSTED_DIR/${basename}-${timestamp}.md"
    else
        echo "FAILED to post"
        exit 1
    fi
}

main "$@"
