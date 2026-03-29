#!/usr/bin/env python3
"""
OpenClaw Skill Manager
Simple tool to fetch skills and manage annotations (like chub CLI)
"""

import json
import sys
import os
from pathlib import Path

REGISTRY_DIR = Path(__file__).parent / "registry"
DIST_DIR = REGISTRY_DIR / "dist"
ANNOTATIONS_FILE = Path(__file__).parent / "annotations" / "openclaw-annotations.yaml"

def load_registry():
    """Load the skills registry"""
    registry_file = DIST_DIR / "registry.json"
    if not registry_file.exists():
        print("❌ Registry not found. Run ./build.sh first.")
        sys.exit(1)
    
    with open(registry_file) as f:
        return json.load(f)

def search_skills(query=None):
    """Search available skills"""
    registry = load_registry()
    skills = registry.get("skills", [])
    
    if not query:
        print(f"\n📚 Available skills ({len(skills)} total):\n")
        for skill in skills:
            print(f"  openclaw/{skill['name']}")
            print(f"    {skill['description']}")
            print()
    else:
        query_lower = query.lower()
        matches = [s for s in skills if query_lower in s["name"].lower() or query_lower in s["description"].lower()]
        
        if matches:
            print(f"\n🔍 Found {len(matches)} match(es) for '{query}':\n")
            for skill in matches:
                print(f"  openclaw/{skill['name']}")
                print(f"    {skill['description']}")
                print()
        else:
            print(f"❌ No matches found for '{query}'")

def get_skill(skill_id):
    """Fetch a skill by ID"""
    if skill_id.startswith("openclaw/"):
        skill_id = skill_id.replace("openclaw/", "")
    
    # Find skill in registry to get correct path
    registry = load_registry()
    skill_path = None
    for skill in registry.get("skills", []):
        if skill["name"] == skill_id or skill["id"] == f"openclaw/{skill_id}":
            skill_path = skill["path"]
            break
    
    if skill_path:
        skill_file = DIST_DIR / skill_path
    else:
        # Fallback: try common patterns
        skill_file = DIST_DIR / "openclaw" / "skills" / skill_id / "SKILL.md"
    
    if not skill_file.exists():
        print(f"❌ Skill not found: {skill_id}")
        sys.exit(1)
    
    with open(skill_file) as f:
        content = f.read()
    
    # Check for annotations
    annotations = load_annotations()
    skill_annotations = annotations.get(f"openclaw/{skill_id}", [])
    
    print(content)
    
    if skill_annotations:
        print("\n" + "="*60)
        print("📌 ANNOTATIONS (local learnings):")
        print("="*60)
        for note in skill_annotations:
            print(f"  • {note}")
        print()

def load_annotations():
    """Load annotations from YAML"""
    if not ANNOTATIONS_FILE.exists():
        return {}
    
    # Simple YAML parser for our format
    annotations = {}
    current_skill = None
    
    with open(ANNOTATIONS_FILE) as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            
            if line.endswith(":") and not line.startswith(" "):
                current_skill = line[:-1]
                annotations[current_skill] = []
            elif line.startswith("  - ") and current_skill:
                note = line[4:].strip('"')
                annotations[current_skill].append(note)
    
    return annotations
def annotate_skill(skill_id, note):
    """Add an annotation to a skill"""
    if skill_id.startswith("openclaw/"):
        skill_id = skill_id.replace("openclaw/", "")
    
    full_id = f"openclaw/{skill_id}"
    
    # Verify skill exists
    skill_file = DIST_DIR / "openclaw" / "skills" / skill_id / "SKILL.md"
    if not skill_file.exists():
        print(f"❌ Skill not found: {skill_id}")
        sys.exit(1)
    
    # Load existing annotations
    annotations = load_annotations()
    
    if full_id not in annotations:
        annotations[full_id] = []
    
    annotations[full_id].append(note)
    
    # Save back to YAML
    ANNOTATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ANNOTATIONS_FILE, 'w') as f:
        f.write("# Annotations for OpenClaw Skills\n")
        f.write("# These are local notes attached to skills that persist across sessions\n")
        f.write("# Format: skill_id: [list of annotations]\n\n")
        
        for sid, notes in annotations.items():
            f.write(f"{sid}:\n")
            for n in notes:
                f.write(f'  - "{n}"\n')
            f.write("\n")
    
    print(f"✅ Annotation added to {full_id}")
    print(f"   Note: {note}")

def list_annotations():
    """List all annotations"""
    annotations = load_annotations()
    
    if not annotations:
        print("📭 No annotations yet.")
        return
    
    print("\n📌 All Annotations:\n")
    for skill_id, notes in annotations.items():
        print(f"{skill_id}:")
        for note in notes:
            print(f"  • {note}")
        print()

def main():
    if len(sys.argv) < 2:
        print("OpenClaw Skill Manager")
        print("")
        print("Usage:")
        print("  python3 skill-manager.py search [query]  # Search skills")
        print("  python3 skill-manager.py get <id>        # Fetch a skill")
        print("  python3 skill-manager.py annotate <id> <note>  # Add annotation")
        print("  python3 skill-manager.py annotations     # List all annotations")
        print("")
        print("Examples:")
        print("  python3 skill-manager.py search tutor")
        print("  python3 skill-manager.py get sol-academic-tutor")
        print("  python3 skill-manager.py annotate dax-personal-trainer 'Add mobility work'")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else None
        search_skills(query)
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("❌ Usage: python3 skill-manager.py get <skill-id>")
            sys.exit(1)
        get_skill(sys.argv[2])
    
    elif command == "annotate":
        if len(sys.argv) < 4:
            print("❌ Usage: python3 skill-manager.py annotate <skill-id> <note>")
            sys.exit(1)
        skill_id = sys.argv[2]
        note = " ".join(sys.argv[3:])
        annotate_skill(skill_id, note)
    
    elif command == "annotations":
        list_annotations()
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
