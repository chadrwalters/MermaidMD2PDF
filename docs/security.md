# Security Features

This document outlines the security features and scanning tools implemented in the MermaidMD2PDF project.

## Overview

The project implements multiple layers of security scanning to ensure code quality and identify potential vulnerabilities:

1. Dependency Scanning
   - Python dependencies (Safety)
   - Node.js dependencies (Snyk)
2. Code Analysis
   - CodeQL analysis for Python and JavaScript
   - Weekly scheduled security scans

## Dependency Scanning

### Python Dependencies (Safety)

Safety is used to scan Python dependencies for known vulnerabilities. The scan runs on every push and pull request to the main branch.

Configuration:
- Runs in the CI workflow
- Checks all dependencies in `pyproject.toml`
- Fails the build if high-severity vulnerabilities are found

### Node.js Dependencies (Snyk)

Snyk is used to scan Node.js dependencies for known vulnerabilities. The scan runs on every push and pull request to the main branch.

Configuration:
- Runs in the CI workflow
- Uses Snyk CLI version 1.1260.0
- Requires `SNYK_TOKEN` secret
- Fails the build if high-severity vulnerabilities are found

Known Issues:
- Puppeteer vulnerability (20240216) is mitigated by using system Chromium
- See `.snyk` file for detailed configuration and exclusions

## Code Analysis

### CodeQL Analysis

CodeQL is used to perform static code analysis on both Python and JavaScript code. The analysis runs:
- On every push to main
- On every pull request
- Weekly (Sundays at 01:30 UTC)

Configuration:
- Separate workflow file: `.github/workflows/codeql.yml`
- Configuration file: `.github/codeql-config.yml`
- Analyzes both Python and JavaScript code
- Uses security and quality queries

Paths Analyzed:
- `src/` - Main source code
- `tests/` - Test files
- `scripts/` - Utility scripts

Excluded Paths:
- `node_modules/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `dist/`
- `build/`
- `.git/`

## Security Workflow

1. On every push and pull request:
   - Safety scans Python dependencies
   - Snyk scans Node.js dependencies
   - CodeQL analyzes both Python and JavaScript code

2. Weekly scheduled scan:
   - CodeQL performs a full analysis
   - Results are available in the Security tab

3. Build Requirements:
   - All security scans must pass
   - No high-severity vulnerabilities
   - CodeQL analysis must complete successfully

## Viewing Results

### Dependency Scan Results

1. Safety Results:
   - Available in the CI workflow logs
   - Look for the "Install Safety" step

2. Snyk Results:
   - Available in the CI workflow logs
   - Look for the "Run Snyk security scan" step
   - Also available in the Snyk dashboard

### CodeQL Results

1. In GitHub:
   - Go to the Security tab
   - Select "Code scanning"
   - View alerts by language or severity

2. In Workflow Logs:
   - Find the "CodeQL Analysis" job
   - View detailed results in the logs

## Troubleshooting

### Common Issues

1. Snyk Token Missing
   - Error: "SNYK_TOKEN not found"
   - Solution: Add SNYK_TOKEN to repository secrets

2. CodeQL Build Failures
   - Check build commands in `.github/codeql-config.yml`
   - Verify Python/Node.js versions match CI environment

3. False Positives
   - Review `.snyk` file for exclusions
   - Check CodeQL query results in Security tab

## Best Practices

1. Regular Updates
   - Keep dependencies up to date
   - Review security alerts weekly
   - Update Snyk exclusions as needed

2. Code Changes
   - Run security scans locally before pushing
   - Address high-severity issues immediately
   - Document security-related changes

3. Configuration
   - Review security configurations quarterly
   - Update scanning tools to latest versions
   - Maintain accurate exclusion lists
# Security improvements
