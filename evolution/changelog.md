# Changelog

> Track major system changes and capability additions

## [Unreleased]
*Changes not yet tagged*

---

## [1.0.0] - 2025-02-01 - Genesis

### Added
- Complete directory structure
- Core configuration files
  - `.env` / `.env.example` for secrets
  - `platforms.yaml` for platform configs
  - `settings.yaml` for global settings
  - `notifications.yaml` for alerts
- Personality system
  - `base.md` - Core identity
  - `poster.md` - Social media voice
  - `coder.md` - Technical voice
  - `analyst.md` - Market analysis voice
- Goals system
  - `north-stars.md` - Two core objectives
  - `active-tasks.md` - Task queue
  - `achievements.md` - Milestone tracking
- Memory system
  - `context.md` - Current state
  - `learnings.md` - Knowledge base
  - `relationships.md` - Connection tracking
  - `content-log.md` - Post archive
- Skills
  - `feed-reader` - Content consumption
  - `poster` - Content publishing
  - `content-studio` - Content creation
  - `code-shipper` - Code sharing
  - `market-intel` - Market tracking
  - `memory-sync` - State persistence
- Dashboard
  - Flask web app
  - Activity feed
  - Metrics display
  - Memory viewer
- Logging
  - `activity.jsonl` - Machine format
  - `activity.md` - Human format
- Documentation
  - `INDEX.md` - Central reference

### Notes
- Initial system architecture
- Ready for operational testing
- Moltbook integration pending API key
- X integration pending developer account

---

## Format

```markdown
## [VERSION] - DATE - Title

### Added
- New features

### Changed
- Modified features

### Fixed
- Bug fixes

### Removed
- Removed features

### Notes
- Additional context
```
