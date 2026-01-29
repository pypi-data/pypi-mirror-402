# RFP Kit Future Deployment Verification

## Status: ✅ Prompts Folder Included (with fixes needed)

### Current State

**Source Templates:**
- ✅ `/templates/prompts/` folder exists with 9 rfpkit.*.prompt.md files
- ✅ Correct format: `See: @rfpkit.X.agent.md` (not YAML frontmatter)
- ✅ All files use `rfpkit` prefix (not `speckit`)

**Release Package Script:** `.github/workflows/scripts/create-release-packages.sh`
- ✅ Line 172: `generate_copilot_prompts` function DOES create prompts/ folder
- ❌ **BUG FIXED**: Was using `speckit.*.agent.md` pattern → Changed to `rfpkit.*.agent.md`
- ❌ **BUG FIXED**: Was using YAML frontmatter format → Changed to `See: @` format
- ❌ **BUG FIXED**: Output files used `speckit` prefix → Changed to `rfpkit` prefix

### Fixes Applied

1. **generate_copilot_prompts function** (lines 107-119):
   - Changed: `speckit.*.agent.md` → `rfpkit.*.agent.md`
   - Changed: YAML frontmatter → `See: @${basename}.agent.md` format
   - Result: Matches manual prompts/ folder    - Result: Matches manual prods function   - Result: Matches manual prompts/ folder    - Resu→ `rfpkit.$name.$ext`
                 output                  output                  output                  outpion


                output                  output                  ouc-ki                output                  output   line                output                  output                  ouc-ki        ec Kit (backwards compatible)
2. **Change repo**: Update to your own fork/repo for in2. **Change repo**: Update to your own fork/repo for in2. **Change repo**: Update to your ows

### Next Steps

**Option A: Independent RFP Kit Repository**
```python
# Update src/rfpkit_cli/__init__.py line 638-639:
repo_owner = "sketabchi"  # or your GitHub org
repo_name = "rfpkit"  # your repo name
```

**Option B: Keep Spec Kit Compatibility**
- Leave repo config unchanged
- RFP Kit CLI will download from github/spec-kit releases
- Works only if github/spec-kit include- Works only if github/spec-kit include- Works only if github/spec-kit include- Works only if github/spec-kit include- Works only if github/spec-kit include- Woren- Works only if github/spec-kit include- Works only if github/spec-kit include- Works only if gt package creation (requires Linux or Bash 4+):
cd /Users/sketabchi/dev/SDD/spec-kit
AGENTS=copilot SCRIPTS=sh .github/workflows/scripts/create-release-packages.sh v0.1.0

# Check generated structure:
unzip -l .genreleases/spec-kit-template-copilot-sh-v0.1.0.zip | grep prompts

# Expected output:
# .github/prompts/rfpkit.analyze.prompt.md
# .github/prompts/rfpkit.checklist.prompt.md
# ... (9 total # ... (9 total # ... (9 total # ... COMMENDED# ... (9 A# ... (9 total # ... (9 total # ... (9 total # t i# ... (9 total # ... (9 total # ... (9 totoftwa# ... (9 total # ... (9 tos different (guidelines vs constitution, section vs specify, etc.)
3. Future enhancements will diverge further
4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users e**4. Users expect `rfpkit` templcreate-4. Users expect `rfpkit` templates, n4. Users expect `rfpkit` templates, n4. Users e@ f4. Users expect `rfpkit` ds: rfpkit output filenames
