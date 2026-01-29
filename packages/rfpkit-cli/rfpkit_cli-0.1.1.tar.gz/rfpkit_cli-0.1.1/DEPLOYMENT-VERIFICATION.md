# RFP Kit - Future Deployment Verification

## ✅ Status: Prompts Folder Included (with critical fixes applied)

### Summary

**Question:** Does `rfpkit init` include the `.github/prompts/` folder for future deployments?

**Answer:** YES - with fixes applied to the release package script.

---

## Findings

### 1. Source Templates ✅
- Prompts folder exists: `/templates/prompts/` with 9 files
- Correct naming: `rfpkit.*.prompt.md` format
- Correct content: `See: @rfpkit.X.agent.md` (GitHub Copilot standard)

### 2. Release Script - Fixes Applied ✅

**File:** `.github/workflows/scripts/create-release-packages.sh`

**Changes Made:**

1. **Fixed `generate_copilot_prompts` function** (lines 107-119):
   - Before: `for agent_file in "$agents_dir"/speckit.*.agent.md`
   - After: `for agent_file in "$agents_dir"/rfpkit.*.agent.md`
   - Before: YAML frontmatter `---\nagent: ${basename}\n---`
   - After: Simple reference `See: @${basename}.agent.md`

2. **Fixed `generate_commands` function** (lines 93-99):
   - Before: `"$output_dir/speckit.$name.$ext"`
   - After: `"$output_dir/rfpkit.$name.$ext"`
   - All output files now use `rfpkit` prefix

### 3. Critical Discovery: Repo Configuration ⚠️

**CLI downloads from:** `github/spec-kit` (not your fork!)

**Location:** `src/rfpkit_cli/__init__.py` line 638-639
```python
repo_owner = "github"
repo_name = "spec-kit"
```

**Impact:** CLI will try to download from original Spec Kit repo, which won't have RFP Kit templates.

---

## Recommendations

### Option A: Independent RFP Kit Repository (RECOMMENDED)

**Why:** RFP Kit is a fork with different purpose, terminology, and future trajectory.

**Steps:**
1. Create new GitHub repository (e.g., `sketabchi/rfpkit`)
2. Update CLI repo config:
   ```python
   repo_owner = "sketabchi"  # your username/org
   repo_name = "rfpkit"
   ```
3. Test package creation locally
4. Push code and create first release (v0.1.0)
5. Test `rfpkit init` downloads from your repo

**Benefits:**
- Independent release cycle
- RFP-specific enhancements
- Users get `rfpkit` templates, not `speckit`
- Clear branding separation

### Option B: Local Templates (Testing Only)

Use `--local-template` flag for development:
```bash
rfpkit init my-project --ai copilot --local-template ./path/to/template.zip
```

**Good for:** Local testing, not distribution.

### Option C: Hybrid (Not Recommended)

Keep `github/spec-kit` repo config but contribute RFP templates upstream. This creates confusion and mixing of purposes.

---

## Verification Commands

### Build Package Locally
```bash
# Note: Requires Linux or Bash 4+
cd /Users/sketabchi/dev/SDD/spec-kit
AGENTS=copilot SCRIPTS=sh .github/workflows/scripts/create-release-packages.sh v0.1.0
```

### Check Package Structure
```bash
unzip -l .genreleases/spec-kit-template-copilot-sh-v0.1.0.zip | grep -E "(agents|prompts)"
```

**Expected output:**
```
.github/agents/rfpkit.analyze.agent.md
.github/agents/rfpkit.checklist.agent.md
... (9 agent files)
.github/prompts/rfpkit.analyze.prompt.md
.github/prompts/rfpkit.checklist.prompt.md
... (9 prompt files)
```

---

## Files Modified

1. `.github/workflows/scripts/create-release-packages.sh`
   - `generate_copilot_prompts`: rfpkit pattern + See: @ format
   - `generate_commands`: rfpkit output filenames

---

## Next Actions

1. **Decision:** Choose Option A, B, or C
2. **If Option A:** Update CLI repo config
3. **Test:** Create local package
4. **Deploy:** Push to GitHub and create release
5. **Verify:** Test `rfpkit init` with new repo
