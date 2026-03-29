#!/bin/bash
# Guru v3.0 Update Script — Koan Revolution
# Applies the Zen/Buddhist koan-focused prompt

CRON_ID="fef6c9d8-a3e0-434b-940c-179acffa503a"
PROMPT_FILE="/Users/sirius_bot/.openclaw/workspace/autoresearch/agents/guru/prompt-v3.0.md"

echo "Updating Guru (Spirituality Guide) to v3.0 — Koan Revolution"
echo "============================================================"

# Read the prompt content
PROMPT_CONTENT=$(cat "$PROMPT_FILE")

# Update the cron job with new prompt
openclaw cron update "$CRON_ID" \
  --prompt "$PROMPT_CONTENT" \
  --model "ollama/qwen3.5:9b" \
  --timeout 120 \
  --channel telegram \
  --target "8584092724"

echo ""
echo "✅ Guru updated to v3.0"
echo "📅 Next run: 5:15 AM"
echo "🧘 Koan-style delivery enabled"
echo "📝 Model: Qwen 3.5 (optimized for Zen/Buddhist content)"
