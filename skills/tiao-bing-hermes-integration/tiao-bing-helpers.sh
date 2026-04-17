#!/usr/bin/env bash
# 调兵系统快捷命令
# 用法: source ~/.hermes/scripts/tiao-bing-helpers.sh

UNIFIED="$HOME/.hermes/scripts/tiao-bing-unified.py"

alias copaw='python3 "$UNIFIED" copaw'
alias openclaw='python3 "$UNIFIED" openclaw'
alias opencode='python3 "$UNIFIED" opencode'
alias tiao-status='python3 "$UNIFIED" status'
alias tiao-list='python3 "$UNIFIED" list-agents'

open-web() {
    python3 "$HOME/.hermes/scripts/tiao-bing-open-web.py" "$@"
}
