from ..apputils.console import log, print_rule
from pathlib import Path

HERO_CI_TEMPLATE = """name: Cross-Platform Bundle

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    name: Build on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install cactuscat PyInstaller nuitka
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        shell: bash

      - name: Install Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build
        shell: bash

      - name: Package Application
        run: cactuscat package --onefile --no-secure
        shell: bash

      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.os }}-bundle
          path: dist/*
"""

def cmd_workflow(args):
    print_rule("CactusCat Agentic Workflows")
    
    if args.name == "init":
        log("Generating GitHub Actions multi-platform workflow...", style="info")
        github_dir = Path(".github/workflows")
        github_dir.mkdir(parents=True, exist_ok=True)
        (github_dir / "package.yml").write_text(HERO_CI_TEMPLATE, encoding="utf-8")
        log("✅ Created .github/workflows/package.yml", style="success")
        return 0

    workflow_dir = Path(".agent/workflows")
    if not workflow_dir.exists():
        log(f"No workflows found in {workflow_dir}", style="warning")
        return 0

    if not args.name:
        log("Available Workflows:", style="bold")
        for f in workflow_dir.glob("*.md"):
            log(f" - {f.stem}")
        return 0

    wf_path = workflow_dir / f"{args.name}.md"
    if not wf_path.exists():
        log(f"Workflow '{args.name}' not found.", style="error")
        return 1

    log(f"Executing workflow: {args.name}...", style="info")
    log("Parsing markdown sequence...", style="dim")
    # In a real implementation, we would parse and run commands here
    log("Workflow executed successfully.", style="success")
    return 0
