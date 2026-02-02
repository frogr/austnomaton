#!/bin/bash
# Wrapper that sets restrictive environment to avoid TCC prompts
export HOME="/Users/austn"
export TMPDIR="/Users/austn/.austnomaton/tmp"
mkdir -p "$TMPDIR"
cd /Users/austn/.austnomaton
exec /Users/austn/.austnomaton/scripts/heartbeat.sh
