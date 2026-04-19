#!/usr/bin/env bash
# Robin — Local-dev shell alias installer (contributors only; end-users install from marketplace)
#
# Adds a `claude-robin` alias that runs `claude --plugin-dir <this repo>`,
# so edits to the source are picked up live (via /reload-plugins mid-session).
# End-users should use `/plugin marketplace add waynewangyuxuan/Robin` instead.
#
# Dual-mode: source or execute
#
# Recommended (alias active immediately in current shell):
#   source ./dev-install.sh
#
# Also works as a plain script (alias only active in NEW shells until you
# run `source ~/.zshrc`):
#   ./dev-install.sh
#
# Subcommands:
#   source ./dev-install.sh remove   # or:  ./dev-install.sh remove

# ─── Detect whether we are sourced or executed ──────────
if (return 0 2>/dev/null); then
  _ROBIN_SOURCED=1
else
  _ROBIN_SOURCED=0
fi

# Don't pollute caller's shell options when sourced; fail fast when executed.
[ "$_ROBIN_SOURCED" = "1" ] || set -e

# ─── Resolve repo root (works in bash and zsh, sourced or executed) ──
if [ -n "${BASH_SOURCE[0]:-}" ]; then
  _ROBIN_SCRIPT="${BASH_SOURCE[0]}"
else
  _ROBIN_SCRIPT="${(%):-%x}"   # zsh-only fallback
  [ -z "$_ROBIN_SCRIPT" ] && _ROBIN_SCRIPT="$0"
fi
REPO_ROOT="$(cd "$(dirname "$_ROBIN_SCRIPT")" 2>/dev/null && pwd)"

ALIAS_NAME="claude-robin"
ALIAS_LINE="alias ${ALIAS_NAME}='claude --plugin-dir ${REPO_ROOT}'"
MARKER_BEGIN="# >>> robin plugin alias (managed by dev-install.sh) >>>"
MARKER_END="# <<< robin plugin alias (managed by dev-install.sh) <<<"

# Bail helper: return when sourced, exit when executed
_robin_bail() {
  local code="${1:-0}"
  _robin_cleanup
  if [ "$_ROBIN_SOURCED" = "1" ]; then
    # `return` is valid inside a sourced script in both bash and zsh
    return "$code" 2>/dev/null || true
  else
    exit "$code"
  fi
}

_robin_cleanup() {
  unset -f _robin_detect_rc _robin_sed_inplace 2>/dev/null
  unset _ROBIN_SCRIPT MARKER_BEGIN MARKER_END EXISTING MODE TITLE ALIAS_STATUS 2>/dev/null
}

# ─── Detect shell rc file ───────────────────────────────
_robin_detect_rc() {
  case "$(basename "${SHELL:-/bin/zsh}")" in
    zsh)  echo "$HOME/.zshrc" ;;
    bash)
      if [ -f "$HOME/.bashrc" ]; then
        echo "$HOME/.bashrc"
      else
        echo "$HOME/.bash_profile"
      fi
      ;;
    fish)
      cat >&2 <<EOF
fish shell detected. Add this to ~/.config/fish/config.fish manually:
  alias ${ALIAS_NAME} 'claude --plugin-dir ${REPO_ROOT}'
EOF
      return 1
      ;;
    *)
      cat >&2 <<EOF
Unknown shell ($SHELL). Add this to your shell rc manually:
  ${ALIAS_LINE}
EOF
      return 1
      ;;
  esac
}

if ! RC="$(_robin_detect_rc)"; then
  _robin_bail 1
fi

# ─── Portable in-place edit that follows symlinks ───────
_robin_sed_inplace() {
  local script="$1"
  local file="$2"
  local tmp
  tmp="$(mktemp)"
  sed "$script" "$file" > "$tmp" && cat "$tmp" > "$file"
  rm -f "$tmp"
}

_robin_escape_sed() {
  printf '%s\n' "$1" | sed 's/[[\.*^$/]/\\&/g'
}

# ─── Uninstall ──────────────────────────────────────────
if [ "${1:-}" = "remove" ]; then
  if [ -f "$RC" ] && grep -qF "$MARKER_BEGIN" "$RC"; then
    _robin_sed_inplace "/$(_robin_escape_sed "$MARKER_BEGIN")/,/$(_robin_escape_sed "$MARKER_END")/d" "$RC"
    if [ "$_ROBIN_SOURCED" = "1" ]; then
      unalias "$ALIAS_NAME" 2>/dev/null || true
      echo ""
      echo "  ◆ Robin — Alias removed from $RC and unset in current shell"
      echo ""
    else
      echo ""
      echo "  ◆ Robin — Alias removed from $RC"
      echo ""
    fi
  else
    echo "  Nothing to remove in $RC"
  fi
  _robin_bail 0
fi

# ─── Detect existing install ────────────────────────────
MODE="install"
if [ -f "$RC" ] && grep -qF "$MARKER_BEGIN" "$RC"; then
  EXISTING="$(awk -v b="$MARKER_BEGIN" -v e="$MARKER_END" '
    $0 == b { in_block = 1; next }
    $0 == e { in_block = 0; next }
    in_block && /^alias/ { print; exit }
  ' "$RC")"
  if [ "$EXISTING" = "$ALIAS_LINE" ]; then
    MODE="already"
  else
    MODE="update"
  fi
fi

# ─── Install / Update — write to rc file ────────────────
if [ "$MODE" != "already" ]; then
  if [ -f "$RC" ] && grep -qF "$MARKER_BEGIN" "$RC"; then
    _robin_sed_inplace "/$(_robin_escape_sed "$MARKER_BEGIN")/,/$(_robin_escape_sed "$MARKER_END")/d" "$RC"
  fi
  {
    echo ""
    echo "$MARKER_BEGIN"
    echo "$ALIAS_LINE"
    echo "$MARKER_END"
  } >> "$RC"
fi

# ─── If sourced, define alias in caller's shell now ─────
if [ "$_ROBIN_SOURCED" = "1" ]; then
  eval "$ALIAS_LINE"
  ALIAS_STATUS="active in this shell"
else
  ALIAS_STATUS="run \`source $RC\` to activate (or open a new terminal)"
fi

# ─── Output ─────────────────────────────────────────────
case "$MODE" in
  already) TITLE="Robin — Alias already installed (verified)" ;;
  update)  TITLE="Robin — Alias updated" ;;
  *)       TITLE="Robin — Alias installed" ;;
esac

if command -v gum >/dev/null 2>&1; then
  echo ""
  gum style --border double --padding "1 2" --border-foreground 5 \
    "◆ $TITLE" \
    "" \
    "Shell rc:  $RC" \
    "Alias:     $ALIAS_NAME ($ALIAS_STATUS)" \
    "Plugin:    $REPO_ROOT" \
    "" \
    "Run:     $ALIAS_NAME           # start a Claude Code session with /robin-* available" \
    "Then:    /robin-start <brief>  # inside the session"
  echo ""
else
  cat <<EOF

  ◆ $TITLE

  Shell rc:  $RC
  Alias:     $ALIAS_NAME ($ALIAS_STATUS)
  Plugin:    $REPO_ROOT

  Run:     $ALIAS_NAME           # start a Claude Code session with /robin-* available
  Then:    /robin-start <brief>  # inside the session

EOF
fi

_robin_bail 0
