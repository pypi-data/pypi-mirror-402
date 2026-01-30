from __future__ import annotations

from datetime import datetime


def mit_license(author: str = "", year: str = "") -> str:
    y = year or str(datetime.utcnow().year)
    a = author or "<YOUR NAME>"
    return f"""MIT License

Copyright (c) {y} {a}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def keep_a_changelog() -> str:
    return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Fixed

"""


def contributing_md() -> str:
    return """# Contributing

Thanks for taking the time to contribute!

## Development

- Fork the repo and create your branch from `main`.
- Run tests locally before opening a PR.
- Keep PRs small and focused.

## Commit messages

We recommend Conventional Commits:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `refactor:` refactor without behavior change

## Pull Requests

- Describe the motivation and context.
- Include screenshots or logs when relevant.
- Add tests for new behavior.

"""


def security_md() -> str:
    return """# Security Policy

## Supported Versions

We support the latest minor version.

## Reporting a Vulnerability

Please open a private security advisory on GitHub, or email the maintainers.

"""


def code_of_conduct_md() -> str:
    # Contributor Covenant v2.1 (shortened header + full body)
    return """# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity
and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

- Demonstrating empathy and kindness toward other people
- Being respectful of differing opinions, viewpoints, and experiences
- Giving and gracefully accepting constructive feedback
- Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
- Focusing on what is best not just for us as individuals, but for the
  overall community

Examples of unacceptable behavior include:

- The use of sexualized language or imagery, and sexual attention or advances
- Trolling, insulting or derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or email address,
  without their explicit permission
- Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement.

## Attribution

This Code of Conduct is adapted from the Contributor Covenant, version 2.1.
"""


def readme_md(stack: str, project_name: str = "<PROJECT NAME>") -> str:
    stack_note = {
        "python": "- Run: `pip install -r requirements.txt`\n- Test: `pytest`",
        "node": "- Install: `npm install`\n- Test: `npm test`",
        "go": "- Test: `go test ./...`",
        "rust": "- Test: `cargo test`",
        "generic": "- Add setup instructions for your project",
    }.get(stack, "- Add setup instructions for your project")

    return f"""# {project_name}

One-line description.

## Installation

{stack_note}

## Usage

```bash
# example
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

See [LICENSE](LICENSE).
"""


def issue_template_bug() -> str:
    return """name: Bug Report
about: Report a reproducible bug
labels: [bug]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for filing a bug report!
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: Tell us what you saw.
      placeholder: Steps to reproduce, expected vs actual...
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: Logs
      description: Paste any relevant logs.
      render: shell
    validations:
      required: false
"""


def issue_template_feature() -> str:
    return """name: Feature Request
about: Suggest an idea
labels: [enhancement]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem
      description: What problem are you trying to solve?
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: What do you want to happen?
    validations:
      required: true
"""


def pr_template_md() -> str:
    return """## Summary

Describe what this PR changes and why.

## Checklist

- [ ] Tests added/updated
- [ ] Docs updated
- [ ] Lint/format passes
"""


def workflow_ci(stack: str) -> str:
    if stack == "python":
        return """name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python -m pip install --upgrade pip
      - run: pip install -r requirements.txt
        if: ${{ hashFiles('requirements.txt') != '' }}
      - run: pip install -e .
        if: ${{ hashFiles('pyproject.toml') != '' }}
      - run: pytest
        if: ${{ hashFiles('pytest.ini', 'pyproject.toml', 'setup.cfg') != '' }}
"""
    if stack == "node":
        return """name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
        if: ${{ hashFiles('package-lock.json') != '' }}
      - run: npm install
        if: ${{ hashFiles('package-lock.json') == '' }}
      - run: npm test
"""
    if stack == "go":
        return """name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go test ./...
"""
    if stack == "rust":
        return """name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test
"""

    return """name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Add your tests here"
"""


def workflow_release() -> str:
    return """name: release
on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  github_release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
"""


def release_script(stack: str) -> str:
    # A small helper to bump version + tag; users can adapt.
    return f"""#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/release.sh 0.1.0
VER="${{1:-}}"
if [[ -z "$VER" ]]; then
  echo "Usage: $0 <version>" >&2
  exit 2
fi

echo "Tagging v$VER"
git tag "v$VER"
git push origin "v$VER"

echo "Done. GitHub Actions should create a release for this tag."
"""


# Public template function names used by the CLI (stable API)
def bug_report_yml() -> str:
    return issue_template_bug()


def feature_request_yml() -> str:
    return issue_template_feature()


def pull_request_template_md() -> str:
    return pr_template_md()


def ci_workflow_yml(stack: str) -> str:
    return workflow_ci(stack)


def release_workflow_yml(stack: str) -> str:
    # release workflow is generic for now
    return workflow_release()
