#!/bin/bash
# Simple sync script: pull, then push if changes exist.

cd "$(dirname "$0")/.." || exit

echo "Pulling latest changes..."
git pull origin main

echo "Adding changes..."
git add .
git commit -m "Auto-sync: $(date +'%Y-%m-%d %H:%M:%S')" || echo "Nothing to commit"

echo "Pushing to GitHub..."
git push origin main