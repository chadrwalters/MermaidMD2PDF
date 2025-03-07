---
name: Release Checklist
about: Create a new release
title: 'Release v[VERSION]'
labels: release
assignees: ''
---

## Pre-release Tasks

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md with new version
- [ ] Run full test suite locally
- [ ] Check all dependencies are up to date
- [ ] Verify documentation is up to date
- [ ] Run linting and type checking
- [ ] Build package locally and test installation
- [ ] Test on multiple Python versions (3.8-3.11)
- [ ] Test on multiple operating systems (Linux, macOS, Windows)

## Release Tasks

- [ ] Create a new release on GitHub
- [ ] Tag the release with `v[VERSION]`
- [ ] Write release notes including:
  - Major changes
  - Breaking changes
  - New features
  - Bug fixes
  - Documentation updates
- [ ] Upload release assets:
  - Source code (zip)
  - Source code (tar.gz)
  - Wheel file
  - Documentation PDF

## Post-release Tasks

- [ ] Verify PyPI package is published
- [ ] Verify documentation is deployed
- [ ] Update any example repositories
- [ ] Announce release on:
  - GitHub Discussions
  - Twitter
  - LinkedIn
- [ ] Monitor for any immediate issues
- [ ] Update roadmap for next release

## Notes

- Version format: MAJOR.MINOR.PATCH
- Follow semantic versioning
- Include migration guide if there are breaking changes
- Test the release candidate before final release
