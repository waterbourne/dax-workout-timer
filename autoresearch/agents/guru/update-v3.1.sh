#!/bin/bash
# Guru v3.1 Update Script — No Word Limits
# Removes the 45-55 word constraint, lets koans breathe naturally

CRON_ID="fef6c9d8-a3e0-434b-940c-179acffa503a"
PROMPT_FILE="/Users/sirius_bot/.openclaw/workspace/autoresearch/agents/guru/prompt-v3.1.md"

echo "Updating Guru (Spirituality Guide) to v3.1 — No Word Limits"
echo "==========================================================="
echo ""
echo "Changes from v3.0:"
echo "  ❌ Removed: 45-55 word target"
echo "  ✅ Added: Natural length — koans decide their own size"
echo "  ✅ Added: Two new koan patterns (6 & 7)"
echo "  ✅ Kept: All koan quality rules except word count"
echo ""

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
echo "✅ Guru updated to v3.1"
echo "📅 Next run: 5:15 AM tomorrow"
echo "🧘 Koan-style delivery with natural length"
echo "📝 Model: Qwen 3.5"
