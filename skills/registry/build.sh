#!/bin/bash
# OpenClaw Skills Registry Build Script
# Validates and builds the skill registry

set -e

REGISTRY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$REGISTRY_DIR/openclaw/skills"
DIST_DIR="$REGISTRY_DIR/dist"

echo "=== OpenClaw Skills Registry Build ==="
echo ""

# Check for required files
echo "Checking skills..."
SKILL_COUNT=0
ERRORS=0

for skill_dir in "$SKILLS_DIR"/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        skill_file="$skill_dir/SKILL.md"
        
        if [ ! -f "$skill_file" ]; then
            echo "❌ $skill_name: Missing SKILL.md"
            ((ERRORS++))
            continue
        fi
        
        # Check for frontmatter
        if ! grep -q "^---" "$skill_file"; then
            echo "❌ $skill_name: Missing YAML frontmatter"
            ((ERRORS++))
            continue
        fi
        
        # Check required fields
        if ! grep -q "^name:" "$skill_file"; then
            echo "❌ $skill_name: Missing 'name' in frontmatter"
            ((ERRORS++))
            continue
        fi
        
        if ! grep -q "^description:" "$skill_file"; then
            echo "❌ $skill_name: Missing 'description' in frontmatter"
            ((ERRORS++))
            continue
        fi
        
        if ! grep -q "^metadata:" "$skill_file"; then
            echo "❌ $skill_name: Missing 'metadata' in frontmatter"
            ((ERRORS++))
            continue
        fi
        
        echo "✅ $skill_name"
        ((SKILL_COUNT++))
    fi
done

echo ""
echo "Found $SKILL_COUNT valid skills"

if [ $ERRORS -gt 0 ]; then
    echo "❌ Build failed with $ERRORS errors"
    exit 1
fi

# Create dist directory
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/openclaw/skills"

# Copy skills to dist
cp -r "$SKILLS_DIR"/* "$DIST_DIR/openclaw/skills/"

# Generate registry.json
cat > "$DIST_DIR/registry.json" << EOF
{
  "name": "openclaw",
  "version": "1.0.0",
  "updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "skills": [
$(for skill_dir in "$SKILLS_DIR"/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        skill_file="$skill_dir/SKILL.md"
        # Extract name from frontmatter
        name=$(grep "^name:" "$skill_file" | head -1 | sed 's/name: *//' | tr -d '"')
        # Extract description from frontmatter
        description=$(grep "^description:" "$skill_file" | head -1 | sed 's/description: *//' | tr -d '"')
        echo "    {"
        echo "      \"id\": \"openclaw/$name\","
        echo "      \"name\": \"$name\","
        echo "      \"description\": \"$description\","
        echo "      \"path\": \"openclaw/skills/$skill_name/SKILL.md\""
        echo "    },"
    fi
done | sed '$ s/,$//')
  ]
}
EOF

echo ""
echo "✅ Build complete!"
echo "   Skills: $SKILL_COUNT"
echo "   Output: $DIST_DIR/"
echo ""
echo "To use this registry:"
echo "   chub get openclaw/sol-academic-tutor"
echo "   chub get openclaw/dax-personal-trainer"
echo "   chub get openclaw/guru-spirituality-guide"
