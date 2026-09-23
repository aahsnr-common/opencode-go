#!/usr/bin/env bash
# Symlink the opencode/ and kilo/ staging folders into the CLI config dirs.
# Idempotent: re-running refreshes links; existing real files are backed up
# to <name>.bak (only one generation kept) rather than overwritten.
#
# Usage: ./install.sh [--dry-run]
set -euo pipefail

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCODE_SRC="$REPO_DIR/opencode"
KILO_SRC="$REPO_DIR/kilo"
OPENCODE_DST="${HOME}/.config/opencode"
KILO_DST="${HOME}/.config/kilo"

log() { printf '%s\n' "$*"; }

# link <src-path> <dst-path> — symlink dst -> src, backing up real files.
link() {
  local src="$1" dst="$2" action=""
  if [[ -L "$dst" ]]; then
    action="refresh"
  elif [[ -e "$dst" ]]; then
    action="backup+link"
  else
    action="link"
  fi
  log "  $action: $dst -> $src"
  if [[ $DRY_RUN -eq 1 ]]; then
    return 0
  fi
  if [[ "$action" == "backup+link" ]]; then
    mv "$dst" "$dst.bak"
    log "    backed up previous file to $dst.bak"
  fi
  ln -sfn "$src" "$dst"
}

install_tool() {
  local name="$1" src="$2" dst="$3"
  log "== $name: $src -> $dst =="
  if [[ ! -d "$src" ]]; then
    log "  ERROR: source folder missing: $src" >&2
    exit 1
  fi
  [[ $DRY_RUN -eq 1 ]] || mkdir -p "$dst"
  # Top-level files: config, AGENTS.md, README skipped (repo-only docs).
  for f in "$src"/*.jsonc; do
    [[ -e "$f" ]] && link "$f" "$dst/$(basename "$f")"
  done
  for f in "$src"/AGENTS.md; do
    [[ -e "$f" ]] && link "$f" "$dst/$(basename "$f")"
  done
  # Subdirectories: symlink the whole dir so new files are picked up
  # without re-running the installer.
  for d in agents commands; do
    [[ -d "$src/$d" ]] && link "$src/$d" "$dst/$d"
  done
  log ""
}

log "OpenCode + Kilo config installer${DRY_RUN:+ (dry run)}"
log ""
install_tool "opencode" "$OPENCODE_SRC" "$OPENCODE_DST"
install_tool "kilo" "$KILO_SRC" "$KILO_DST"

if [[ $DRY_RUN -eq 0 ]]; then
  log "Done. Next steps:"
  log "  opencode: run /models, /variants, /connect (see opencode/README.md)"
  log "  kilo:     run 'kilo models' and repoint the placeholder model ids,"
  log "            then /connect (see kilo/README.md)"
  log "Restart each CLI after editing config files."
fi
