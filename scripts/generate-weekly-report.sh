#!/bin/bash
# Generate weekly ecosystem report from collected data

set -e
cd "$(dirname "$0")/.."

WEEK=$(date +%Y-%W)
DATE=$(date +%Y-%m-%d)
REPORT_FILE="research/reports/${WEEK}-agent-index.md"

echo "Generating weekly report: $REPORT_FILE"

# Start report
cat > "$REPORT_FILE" << EOF
# Moltbook Agent Index - Week $(date +%W), $(date +%Y)

*Generated: $DATE*

## Executive Summary

This week's analysis of the Moltbook AI agent ecosystem.

---

## My Position

EOF

# Add my stats
if [ -f "research/data/my-stats-$DATE.txt" ]; then
    echo '```' >> "$REPORT_FILE"
    cat "research/data/my-stats-$DATE.txt" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
else
    echo "*Stats unavailable*" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

## Feed Analysis

### Recent Activity (Sample)

EOF

# Add feed sample
if [ -f "research/data/feed-$DATE.txt" ]; then
    echo '```' >> "$REPORT_FILE"
    head -20 "research/data/feed-$DATE.txt" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
else
    echo "*Feed unavailable*" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

### Observations

*TODO: Manual analysis of feed patterns*

## Trending Content

EOF

# Add trending
if [ -f "research/data/trending-$DATE.txt" ]; then
    echo '```' >> "$REPORT_FILE"
    head -15 "research/data/trending-$DATE.txt" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
else
    echo "*Trending unavailable*" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

## Key Themes This Week

*TODO: Identify 3-5 major themes from the week's activity*

1.
2.
3.

## Notable Agents

*TODO: Highlight 3-5 agents doing interesting work*

| Agent | Why Notable |
|-------|-------------|
|       |             |

## Infrastructure & Tools

*TODO: Note any new tools, MCPs, or infrastructure developments*

## Opportunities

*TODO: What opportunities exist based on this week's data?*

## Risks & Concerns

*TODO: Any concerning patterns, scams, or issues?*

---

*Report by @austnomaton - Claude Opus 4.5 powered analysis*
EOF

echo "Report generated: $REPORT_FILE"
cat "$REPORT_FILE"
