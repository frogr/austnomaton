#!/bin/bash
# Collect Moltbook ecosystem data for research reports

set -e
cd "$(dirname "$0")/.."

# Load env
source .env
export MOLTBOOK_API_KEY

# Output directory
DATA_DIR="research/data"
mkdir -p "$DATA_DIR"

DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TIMESTAMP] Collecting ecosystem data..."

# My stats (baseline)
echo "Collecting my stats..."
molt me > "$DATA_DIR/my-stats-$DATE.txt" 2>&1 || echo "Failed to get my stats"

# Feed snapshot (last 50 posts)
echo "Collecting feed..."
molt feed -n 50 > "$DATA_DIR/feed-$DATE.txt" 2>&1 || echo "Failed to get feed"

# Trending posts
echo "Collecting trending..."
molt trending > "$DATA_DIR/trending-$DATE.txt" 2>&1 || echo "Failed to get trending"

# Timeline (who I follow)
echo "Collecting timeline..."
molt timeline > "$DATA_DIR/timeline-$DATE.txt" 2>&1 || echo "Failed to get timeline"

# Followers and following
echo "Collecting social graph..."
molt followers > "$DATA_DIR/followers-$DATE.txt" 2>&1 || echo "Failed to get followers"
molt following > "$DATA_DIR/following-$DATE.txt" 2>&1 || echo "Failed to get following"

# Notifications (activity around me)
echo "Collecting notifications..."
molt notifications > "$DATA_DIR/notifications-$DATE.txt" 2>&1 || echo "Failed to get notifications"

echo "[$TIMESTAMP] Data collection complete. Files in $DATA_DIR/"
ls -la "$DATA_DIR/"*"$DATE"* 2>/dev/null || echo "No files created today"
