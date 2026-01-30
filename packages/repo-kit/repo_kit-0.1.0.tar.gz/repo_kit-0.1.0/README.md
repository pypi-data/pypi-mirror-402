# repo-kit

**repo-kit** is a tiny CLI that does two things:

1) **scan** a repository and output a **Repo Score (0-100)** with actionable checks
2) **apply** a "professional open-source kit" (README skeleton, License, contributing docs, GitHub templates, CI, Release, Changelog)
3) **badge** to generate and embed a **local score badge SVG** + common GitHub badges

> Goal: make repos look and feel professional in one command — without nuking existing files.

---

## Install

```bash
pipx install repo-kit
# or
pip install repo-kit
```

## Quickstart

```bash
# scan a local repo
repo-kit scan .

# scan a GitHub repo (clones to a temp dir)
repo-kit scan https://github.com/OWNER/REPO

# apply templates (safe by default: won't overwrite existing files)
repo-kit apply --stack python

# generate/update badges
repo-kit badge
```

## Commands

### `repo-kit scan <path-or-github-url>`

- prints a score and checklist
- can emit JSON for CI usage

```bash
repo-kit scan . --format json > repo-kit-report.json
```

### `repo-kit apply`

Generates missing files and directories.

```bash
repo-kit apply --stack node
repo-kit apply --stack python --force   # overwrite existing files
```

### `repo-kit badge`

- creates `./.github/repo-score.svg`
- inserts badges into README (best-effort)

```bash
repo-kit badge --no-shields
```

---

## Repo Score checks (v0.1)

- README presence + basic sections
- LICENSE
- CONTRIBUTING
- CODE_OF_CONDUCT
- Issue templates + PR template
- CI workflow
- Release workflow
- CHANGELOG
- Security policy stub

---

## GitHub Action (example)

Put this in `.github/workflows/repo-kit.yml`:

```yaml
name: repo-kit
on:
  pull_request:
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install repo-kit
      - run: repo-kit scan . --format json > repo-kit-report.json
      - uses: actions/upload-artifact@v4
        with:
          name: repo-kit-report
          path: repo-kit-report.json
```

---

## License

MIT
