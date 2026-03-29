#!/bin/bash
# Guru v2.1 Prompt Update Script
# Applies the evolved prompt with rotation system, no strict word limits

set -e

PROMPT_FILE="/Users/sirius_bot/.openclaw/workspace/autoresearch/agents/guru/prompt-v2.1.md"
CRON_ID="fef6c9d8-a3e0-434b-940c-179acffa503a"

echo "=== Guru v2.1 Update ==="
echo "Date: $(date)"
echo ""

# Verify prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompt file not found: $PROMPT_FILE"
    exit 1
fi

# Read the prompt
PROMPT=$(cat "$PROMPT_FILE")

echo "Prompt file verified: $(wc -w < "$PROMPT_FILE") words"
echo ""

# Update the cron job
echo "Updating cron job $CRON_ID..."
openclaw cron update "$CRON_ID" --prompt "$PROMPT"

echo ""
echo "=== Update Complete ==="
echo ""
echo "Changes applied:"
echo "  • Rotation system: 7 themes (Mon-Stoic, Tue-Zen, Wed-Gita, Thu-Stoic, Fri-Zen, Sat-Gita, Sun-Integration)"
echo "  • Structure: Observation → Insight → Action"
echo "  • Hook: Concrete daily life observation (not abstract questions)"
echo "  • Attribution: Direct quote format (Name: \"quote\")"
echo "  • Length: Natural — not forced, not rambling"
echo ""
echo "Next steps:"
echo "  1. Monitor tomorrow's 5:15 AM delivery"
echo "  2. Observe if message feels natural in length"
echo "  3. Iterate if needed"
