#!/usr/bin/env bash
set -euo pipefail

# === Fill these two lines ===
GITHUB_USER="YOUR_USERNAME_HERE"
REPO_NAME="auntie-jummys-shop"
PRIVATE="true"   # "true" for private, "false" for public
# ============================

# Check deps
command -v git >/dev/null || { echo "git not found"; exit 1; }
command -v gh >/dev/null || echo "Tip: Install GitHub CLI for auto repo creation: https://cli.github.com/"

# Create repo via GitHub CLI if available
if command -v gh >/dev/null; then
  if [ "$PRIVATE" = "true" ]; then
    gh repo create "$GITHUB_USER/$REPO_NAME" --private -y
  else
    gh repo create "$GITHUB_USER/$REPO_NAME" --public -y
  fi
  REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
else
  echo "GitHub CLI not found. Create a repo manually at https://github.com/new and set REMOTE_URL below."
  REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
fi

# Init and push
git init
git add .
git commit -m "Initial import: Auntie Jummy’s Candy & Snacks (Django + Square)"
git branch -M main
git remote add origin "$REMOTE_URL"
git push -u origin main

echo "Done! Repo pushed to $REMOTE_URL"
echo "Next: connect this repo on Render → New → Web Service."
