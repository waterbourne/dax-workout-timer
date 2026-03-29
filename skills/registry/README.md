# OpenClaw Skills Registry

Private skill registry for OpenClaw agents.

## Structure

```
registry/
  openclaw/
    skills/
      sol-academic-tutor/     # Academic tutor for ages 6-8
      dax-personal-trainer/   # Bodyweight fitness trainer
      guru-spirituality-guide/# Morning contemplation guide
```

## Usage

### Install chub CLI
```bash
npm install -g @aisuite/chub
```

### Configure to use this registry
```bash
# Edit ~/.chub/config.yaml
sources:
  - name: public
    url: https://cdn.aichub.org/v1
  - name: openclaw
    path: /Users/sirius_bot/.openclaw/workspace/skills/registry
```

### Search skills
```bash
chub search "academic tutor" --source openclaw
chub search "fitness" --source openclaw
```

### Fetch a skill
```bash
chub get openclaw/sol-academic-tutor
chub get openclaw/dax-personal-trainer
chub get openclaw/guru-spirituality-guide
```

## Adding New Skills

1. Create directory: `registry/openclaw/skills/<skill-name>/`
2. Add `SKILL.md` with YAML frontmatter
3. Run `./build.sh` to validate and build
4. Commit changes

## Skill Format

See [Content Guide](https://github.com/andrewyng/context-hub/blob/main/docs/content-guide.md) for full specification.

### Required frontmatter:
```yaml
---
name: skill-name
description: "Short description"
metadata:
  revision: 1
  updated-on: "2026-03-16"
  source: maintainer|community
  tags: "tag1,tag2,tag3"
---
```

## Annotations

Agents can annotate skills locally:

```bash
chub annotate openclaw/sol-academic-tutor "Works better with 50-word hooks"
chub annotate openclaw/dax-personal-trainer "Add more mobility work on Mondays"
```

Annotations are stored in `~/.chub/annotations/` and persist across sessions.

## Contributing

1. Test skill thoroughly before adding
2. Follow naming convention: `<agent>-<role>`
3. Include evolution notes (what you learned from experiments)
4. Document anti-patterns (what NOT to do)
5. Update revision number when modifying
