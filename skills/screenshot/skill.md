# Screenshot Skill

Capture screenshots with CleanShot X, upload to R2, get CDN URL.

## Usage

```
/screenshot [type] [name]
```

**Types:**
- `area` - Select area to capture (default)
- `window` - Capture a window
- `full` - Full screen
- `file <path>` - Upload existing file

**Examples:**
```
/screenshot area dashboard-v2
/screenshot window terminal-output
/screenshot file ~/Desktop/diagram.png
```

## Output

Returns markdown image link ready to paste:
```
![description](https://pub-4eb969bde4bb4059bbf3f67a0c9bd513.r2.dev/screenshots/2026-02-02-dashboard-v2.png)
```

## Requirements

- CleanShot X installed (falls back to macOS screencapture)
- R2 credentials in .env
