#!/usr/bin/env bash
# Copy data_jobs.duckdb from origin/main into a directory, without changing the current branch.
# Usage: get_db.sh <dest_dir>
set -euo pipefail
dest="${1:?usage: get_db.sh <dest_dir>}"
repo="$(git rev-parse --show-toplevel)"
mkdir -p "$dest"
git -C "$repo" fetch origin main --quiet
git -C "$repo" show origin/main:data_jobs.duckdb > "$dest/data_jobs.duckdb"
ls -la "$dest/data_jobs.duckdb"
