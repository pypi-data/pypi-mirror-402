# Release Process

This document describes the automated release process for `cognite-function-apps` using [release-please](https://github.com/googleapis/release-please).

## Overview

Our release process is designed to:

- **Fully automate releases** based on conventional commit messages
- **Automatically determine version bumps** (major/minor/patch) from commit types
- **Generate changelogs** automatically from commit history
- **Create release PRs** that update versions and CHANGELOG.md
- **Publish to PyPI** automatically when release PRs are merged
- **Comply with GitHub environment protection rules** (CD environment deploys from `main` branch)

## How It Works

### The Automated Flow

1. **You write code** using conventional commit messages (see below)
2. **release-please** analyzes commits and creates/updates a release PR
3. **You review and merge** the release PR
4. **release-please** creates a GitHub Release with tag
5. **GitHub Actions** automatically publishes to PyPI

### What release-please Does

When you push commits to `main` using conventional commit format:

1. **Analyzes commits** since the last release
2. **Determines version bump**:
   - `fix:` → patch version (0.3.2 → 0.3.3)
   - `feat:` → minor version (0.3.2 → 0.4.0)
   - `feat!:` or `BREAKING CHANGE:` → minor version before 1.0 (0.3.2 → 0.4.0), major version after 1.0 (1.0.0 → 2.0.0)
3. **Creates/updates a release PR** that includes:
   - Version bump in `pyproject.toml` and `_version.py`
   - Generated CHANGELOG.md with all changes
   - Commit message: `chore(main): release X.Y.Z`
4. **When you merge the PR**:
   - Creates a GitHub Release with tag `vX.Y.Z`
   - Publishes the changelog notes
5. **PyPI publication** happens automatically via the publish workflow

## Conventional Commits

### Format

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Common Types

- `feat:` - New feature (triggers **minor** version bump)
- `fix:` - Bug fix (triggers **patch** version bump)
- `feat!:` or `BREAKING CHANGE:` - Breaking change (triggers **minor** version bump before 1.0, **major** version bump after 1.0)
- `docs:` - Documentation changes (included in changelog)
- `refactor:` - Code refactoring (included in changelog)
- `perf:` - Performance improvements (included in changelog)
- `test:` - Test changes (hidden from changelog)
- `build:` - Build system changes (hidden from changelog)
- `ci:` - CI/CD changes (hidden from changelog)
- `chore:` - Other changes (hidden from changelog)

### Examples

**Feature (minor bump):**

```bash
git commit -m "feat: add support for custom error handlers

This adds a new error_handler parameter to FunctionApp that allows
users to customize error handling behavior."
```

**Bug fix (patch bump):**

```bash
git commit -m "fix: handle None values in type conversion

Previously None values would cause validation errors. Now they are
properly handled for optional fields."
```

**Breaking change (minor bump before 1.0, major bump after 1.0):**

```bash
git commit -m "feat!: change DependencyRegistry API

BREAKING CHANGE: The register() method now requires an explicit
target_type parameter. Update all calls from register(provider)
to register(provider, target_type=MyType)."
```

**Documentation:**

```bash
git commit -m "docs: update release process documentation"
```

**Refactoring:**

```bash
git commit -m "refactor: simplify route matching logic"
```

## Release Workflow

### Step 1: Develop with Conventional Commits

When developing features or fixing bugs, use conventional commit messages:

```bash
# Feature work
git commit -m "feat: add batch processing support"
git commit -m "test: add tests for batch processing"
git commit -m "docs: document batch processing API"

# Push to main (or merge PR to main)
git push origin main
```

### Step 2: release-please Creates/Updates Release PR

After your commits are pushed to `main`, release-please will:

- Automatically create or update a release PR
- PR title will be: `chore(main): release X.Y.Z`
- PR will include:
  - Version updates in `pyproject.toml` and `_version.py`
  - Generated CHANGELOG.md with all changes since last release
  - Proper semantic version based on commit types

**The PR is cumulative**: If you push more commits before merging, release-please will update the PR to include them.

### Step 3: Review the Release PR

1. Check the version bump is correct
2. Review the generated CHANGELOG
3. Ensure all changes are included
4. Get required approvals per your security policy

**Note:** You can continue pushing commits to `main` while the release PR is open. release-please will keep updating it.

### Step 4: Merge the Release PR

When ready to release:

1. Merge the release PR into `main`
2. release-please will automatically:
   - Create a GitHub Release with tag `vX.Y.Z`
   - Include the changelog in the release notes
   - Mark the release as published

### Step 5: Automatic PyPI Publication

After the release PR is merged, the `python-publish.yml` workflow will:

- Detect the release-please commit (starts with `chore(main):`)
- Build the package
- Publish to PyPI using the version from `_version.py`

## Checking Release Status

### View the Release PR

Go to: [Pull Requests](https://github.com/cognitedata/cognite-function-apps/pulls)

Look for a PR titled `chore(main): release X.Y.Z` created by `github-actions[bot]`

### View Releases

Go to: [Releases](https://github.com/cognitedata/cognite-function-apps/releases)

All releases with changelogs are listed here.

### View Published Packages

Check PyPI: <https://pypi.org/project/cognite-function-apps/>

## Manual Version Bumps (Emergency Use Only)

If you need to force a specific version bump without conventional commits:

1. Create a commit with the desired conventional commit type
2. Or manually edit `.release-please-manifest.json` and create a PR

**Generally, you should rely on conventional commits for version management.**

## Important Notes

### Conventional Commits Are Required

- **All commits to `main` should use conventional commit format**
- This is how release-please determines version bumps
- Use commit types consistently (`feat:`, `fix:`, etc.)

### Release PR Behavior

- release-please keeps **one open release PR** at a time
- New commits update the existing PR until it's merged
- You can merge the PR whenever you're ready to release

### Version Files

The following files are automatically updated by release-please:

- `pyproject.toml` - Package version
- `src/cognite_function_apps/_version.py` - Runtime version
- `CHANGELOG.md` - Generated changelog (created if it doesn't exist)

**Do not manually edit these files for releases.** release-please manages them.

### Breaking Changes

To indicate a breaking change, use one of:

- `feat!:` or `fix!:` (note the `!`)
- Include `BREAKING CHANGE:` in commit footer

**Version bump behavior:**

- **Before 1.0**: Breaking changes trigger a **minor** version bump (0.3.0 → 0.4.0)
- **After 1.0**: Breaking changes trigger a **major** version bump (1.0.0 → 2.0.0)

This follows the semantic versioning convention that versions before 1.0 are considered unstable, where breaking changes are expected and communicated through minor version increments.

Example:

```bash
git commit -m "feat!: redesign API

BREAKING CHANGE: The FunctionApp constructor now requires a title parameter.
Update all FunctionApp() calls to FunctionApp(title='My App')."
```

### Semantic Versioning

release-please follows [semantic versioning](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes (`feat!:`, `BREAKING CHANGE:`) - only after version 1.0
- **MINOR**: New features (`feat:`), or breaking changes before 1.0 (0.3.0 → 0.4.0)
- **PATCH** (1.0.0 → 1.0.1): Bug fixes (`fix:`)

**Note:** Before version 1.0, breaking changes bump the minor version instead of the major version, following the semantic versioning convention that 0.x versions are considered unstable.

## Troubleshooting

### No release PR is created

- Check your commits use conventional commit format
- Ensure commits include `feat:` or `fix:` (not just `chore:` or `docs:`)
- Check GitHub Actions logs for the `release-please` workflow

### Wrong version bump

- Review your commit messages
- Use `feat:` for new features (minor bump)
- Use `fix:` for bug fixes (patch bump)
- Use `feat!:` or `BREAKING CHANGE:` for breaking changes (minor bump before 1.0, major bump after 1.0)

### PyPI publish fails

- Check that the `PYPI_API_TOKEN` secret is set correctly
- Verify the version doesn't already exist on PyPI
- Check the `python-publish.yml` workflow logs

### Want to skip a release

- Don't merge the release PR
- Continue pushing commits to `main`
- The release PR will accumulate all changes until you merge it

## Migration from Manual Process

If you have existing releases, release-please will:

- Start from the version in `.release-please-manifest.json` (currently `0.3.2`)
- Analyze new commits since the last release
- Create appropriate version bumps based on commit types

## Benefits of This Process

- ✅ **Fully automated** - no manual version updates needed
- ✅ **Consistent versioning** - semantic versioning enforced by commit types
- ✅ **Automatic changelogs** - generated from commit messages
- ✅ **No merge conflicts** - only release-please touches version files
- ✅ **Flexible timing** - merge the release PR when you're ready
- ✅ **Compliance** - all releases go through PR review
- ✅ **Clean git history** - conventional commits provide clear intent

## References

- [release-please documentation](https://github.com/googleapis/release-please)
- [Conventional Commits specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
