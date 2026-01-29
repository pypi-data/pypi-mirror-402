# Local Development Guide

This guide shows how to iterate on the `rfpkit` CLI locally without publishing a release or committing to `main` first.

> Scripts have both Bash (`.sh`) and PowerShell (`.ps1`) variants. The CLI auto-selects based on OS unless you pass `--script sh|ps`.

## 1. Clone and Switch Branches

```bash
git clone https://github.com/sketabchi/rfpkit.git
cd rfpkit
# Work on a feature branch
git checkout -b your-feature-branch
```

## 2. Run the CLI Directly (Fastest Feedback)

You can execute the CLI via the module entrypoint without installing anything:

```bash
# From repo root
python -m src.rfpkit_cli --help
python -m src.rfpkit_cli init demo-project --ai copilot --ignore-agent-tools --script sh
```

If you prefer invoking the script file style (uses shebang):

```bash
python src/rfpkit_cli/__init__.py init demo-project --script ps
```

## 3. Use Editable Install (Isolated Environment)

Create an isolated environment using `uv` so dependencies resolve exactly like end users get them:

```bash
# Create & activate virtual env (uv auto-manages .venv)
uv venv
source .venv/bin/activate  # or on Windows PowerShell: .venv\Scripts\Activate.ps1

# Install project in editable mode
uv pip install -e .

# Now 'rfpkit' entrypoint is available
rfpkit --help
```

Re-running after code edits requires no reinstall because of editable mode.

## 4. Invoke with uvx Directly From Git (Current Branch)

`uvx` can run from a local path (or a Git ref) to simulate user flows:

```bash
uvx --from . rfpkit init demo-uvx --ai copilot --ignore-agent-tools --script sh
```

You can also point uvx at a specific branch without merging:

```bash
# Push your working branch first
git push origin your-feature-branch
uvx --from git+https://github.com/sketabchi/rfpkit.git@your-feature-branch rfpkit init demo-branch-test --script ps
```

### 4a. Absolute Path uvx (Run From Anywhere)

If you're in another directory, use an absolute path instead of `.`:

```bash
uvx --from /path/to/rfpkit rfpkit --help
uvx --from /path/to/rfpkit rfpkit init demo-anywhere --ai copilot --ignore-agent-tools --script sh
```

Set an environment variable for convenience:

```bash
export RFPKIT_SRC=/path/to/rfpkit
uvx --from "$RFPKIT_SRC" rfpkit init demo-env --ai copilot --ignore-agent-tools --script ps
```

(Optional) Define a shell function:

```bash
rfpkit-dev() { uvx --from /path/to/rfpkit rfpkit "$@"; }
# Then
rfpkit-dev --help
```

## 5. Testing Script Permission Logic

After running an `init`, check that shell scripts are executable on POSIX systems:

```bash
ls -l scripts | grep .sh
# Expect owner execute bit (e.g. -rwxr-xr-x)
```

On Windows you will instead use the `.ps1` scripts (no chmod needed).

## 6. Run Lint / Basic Checks (Add Your Own)

Currently no enforced lint config is bundled, but you can quickly sanity check importability:

```bash
python -c "import rfpkit_cli; print('Import OK')"
```

## 7. Build a Wheel Locally (Optional)

Validate packaging before publishing:

```bash
uv build
ls dist/
```

Install the built artifact into a fresh throwaway environment if needed.

## 8. Using a Temporary Workspace

When testing `init --here` in a dirty directory, create a temp workspace:

```bash
mkdir /tmp/rfp-test && cd /tmp/rfp-test
python -m src.rfpkit_cli init --here --ai copilot --ignore-agent-tools --script sh  # if repo copied here
```

Or copy only the modified CLI portion if you want a lighter sandbox.

## 9. Debug Network / TLS Skips

If you need to bypass TLS validation while experimenting:

```bash
rfpkit check --skip-tls
rfpkit init demo --skip-tls --ai copilot --ignore-agent-tools --script ps
```

(Use only for local experimentation.)

## 10. Rapid Edit Loop Summary

| Action | Command |
|--------|---------|  
| Run CLI directly | `python -m src.rfpkit_cli --help` |
| Editable install | `uv pip install -e .` then `rfpkit ...` |
| Local uvx run (repo root) | `uvx --from . rfpkit ...` |
| Local uvx run (abs path) | `uvx --from /path/to/rfpkit rfpkit ...` |
| Git branch uvx | `uvx --from git+URL@branch rfpkit ...` |

```bash
rm -rf .venv dist build *.egg-info
```

## 12. Common Issues

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: typer` | Run `uv pip install -e .` |
| Scripts not executable (Linux) | Re-run init or `chmod +x scripts/*.sh` |
| Git step skipped | You passed `--no-git` or Git not installed |
| Wrong script type downloaded | Pass `--script sh` or `--script ps` explicitly |
| TLS errors on corporate network | Try `--skip-tls` (not for production) |

## 13. Next Steps

- Update docs and run through Quick Start using your modified CLI
- Open a PR when satisfied
- (Optional) Tag a release once changes land in `main`
