# CLAUDE.md

**For detailed development guidelines, code standards, and architecture documentation, see [AGENTS.md](AGENTS.md).**

This file is kept minimal to avoid duplication. All agent instructions and project documentation are maintained in AGENTS.md.

## Quick Links

- **Project overview and standards**: [AGENTS.md](AGENTS.md)
- **Release process**: [RELEASING.md](RELEASING.md)
- **Contributing guide**: [docs/contributing.md](docs/contributing.md)

## Quick Reference

### Running Commands

```bash
# Run tests
uv run pytest

# Run type checker
uv run pyright

# Serve docs locally
mkdocs serve
```

### Commit Format (Required)

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated releases.

```bash
# Feature (minor bump)
git commit -m "feat: add new feature"

# Bug fix (patch bump)
git commit -m "fix: resolve bug"

# Breaking change (major bump)
git commit -m "feat!: breaking change

BREAKING CHANGE: detailed explanation"
```

See [AGENTS.md](AGENTS.md) for complete commit guidelines and project standards.
