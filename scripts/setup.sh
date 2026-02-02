#!/bin/bash
#
# Austnomaton Setup Script
# Initializes the environment for a new installation
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Austnomaton Setup${NC}"
echo "=================="
echo

# Get installation directory
INSTALL_DIR="${1:-$HOME/.austnomaton}"
echo -e "Installation directory: ${YELLOW}$INSTALL_DIR${NC}"

# Check if already exists
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Warning: Directory already exists${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$INSTALL_DIR"/{config,content,dashboard/templates,evolution,goals,logs,memory,personality,projects,queue/archive,queue/posted,research/reports,scripts,skills,tools}

# Copy example files if this script is run from a clone
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$REPO_ROOT/.env.example" ]; then
    echo "Copying example files..."
    cp "$REPO_ROOT/.env.example" "$INSTALL_DIR/.env.example"

    if [ ! -f "$INSTALL_DIR/.env" ]; then
        cp "$REPO_ROOT/.env.example" "$INSTALL_DIR/.env"
        echo -e "${YELLOW}Created .env from example - please edit with your API keys${NC}"
    fi
fi

# Copy essential files
for file in CLAUDE.md INDEX.md .gitignore; do
    if [ -f "$REPO_ROOT/$file" ] && [ ! -f "$INSTALL_DIR/$file" ]; then
        cp "$REPO_ROOT/$file" "$INSTALL_DIR/$file"
    fi
done

# Initialize memory/context.md if not exists
if [ ! -f "$INSTALL_DIR/memory/context.md" ]; then
    cat > "$INSTALL_DIR/memory/context.md" << 'EOF'
# Current Context

> Rolling state of what I'm working on and what matters now

## Last Updated
$(date -u +"%Y-%m-%d %H:%M UTC")

## Status: INITIALIZING

First run! Context will be populated as sessions progress.

## Notes
- Update this file at the end of each session
- Track what was done and what needs attention next
EOF
    echo "Initialized memory/context.md"
fi

# Initialize goals/active-tasks.md if not exists
if [ ! -f "$INSTALL_DIR/goals/active-tasks.md" ]; then
    cat > "$INSTALL_DIR/goals/active-tasks.md" << 'EOF'
# Active Tasks

## This Session
- [ ] Complete setup
- [ ] Configure API credentials in .env
- [ ] Run first heartbeat

## Backlog
- Add more tasks here as needed
EOF
    echo "Initialized goals/active-tasks.md"
fi

# Initialize projects/ACTIVE.md if not exists
if [ ! -f "$INSTALL_DIR/projects/ACTIVE.md" ]; then
    cat > "$INSTALL_DIR/projects/ACTIVE.md" << 'EOF'
# Active Projects

> What the agent is currently building.

## Currently Building

Nothing yet - add your first project here!

## Ideas Backlog
- First project idea
- Second project idea
EOF
    echo "Initialized projects/ACTIVE.md"
fi

# Create log files
touch "$INSTALL_DIR/logs/activity.jsonl"
touch "$INSTALL_DIR/logs/heartbeat.log"

echo
echo -e "${GREEN}Setup complete!${NC}"
echo
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/.env with your API keys"
echo "2. Customize personality files in $INSTALL_DIR/personality/"
echo "3. Start the dashboard: cd $INSTALL_DIR/dashboard && python app.py"
echo "4. Run your first session with Claude Code"
echo
