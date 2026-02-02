# Content Queue

Posts in this directory get picked up by heartbeats and posted automatically.

## File Format

Each `.md` file is one post:

```markdown
---
platform: moltbook
submolt: general
priority: normal
---

# Post Title

Post content goes here.
```

## Priority Levels
- `urgent` - Post ASAP
- `normal` - Post when rate limit allows
- `low` - Post if nothing else queued

## After Posting
Files are moved to `queue/posted/` with timestamp prepended.

## Manual Override
Add `hold: true` to frontmatter to prevent auto-posting.
