# Installation Guide

## Prerequisites

- **Linux/macOS/Windows**
- AI coding agent: [GitHub Copilot](https://code.visualstudio.com/) (recommended), [Claude Code](https://www.anthropic.com/claude-code), [Cursor](https://www.cursor.com/), [Gemini CLI](https://github.com/google-gemini/gemini-cli), or any [supported AI agent](https://github.com/sketabchi/rfpkit#-supported-ai-agents)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation

### Initialize a New RFP Project

The easiest way to get started is to initialize a new RFP project:

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <PROJECT_NAME>
```

Or initialize in the current directory:

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init .
# or use the --here flag
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init --here
```

### Specify AI Agent

You can proactively specify your AI agent during initialization:

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <project_name> --ai copilot
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <project_name> --ai claude
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <project_name> --ai cursor-agent
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <project_name> --ai gemini
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:

- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <project_name> --script sh
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <project_name> --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for tools:

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <project_name> --ai copilot --ignore-agent-tools
```

## Verification

After initialization, you should see the following commands available in your AI agent:

- `/rfpkit.analyze` - Analyze RFP document
- `/rfpkit.guidelines` - Create structured guidelines
- `/rfpkit.strategy` - Develop win strategy
- `/rfpkit.section` - Draft proposal sections
- `/rfpkit.compliance` - Verify compliance

The `scripts/` directory will contain both `.sh` and `.ps1` scripts.

## Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
