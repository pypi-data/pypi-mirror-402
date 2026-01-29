# Quick Start Guide

This guide will help you get started with RFP response development using RFP Kit.

> [!NOTE]
> All automation scripts provide both Bash (`.sh`) and PowerShell (`.ps1`) variants. The `rfpkit` CLI auto-selects based on OS unless you pass `--script sh|ps`.

## The 7-Step RFP Response Process

### Step 1: Install RFP Kit

**In your terminal**, run the `rfpkit` CLI command to initialize your project:

```bash
# Create a new project directory
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <PROJECT_NAME>

# OR initialize in the current directory
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init .
```

Pick script type explicitly (optional):

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <PROJECT_NAME> --script ps  # Force PowerShell
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init <PROJECT_NAME> --script sh  # Force POSIX shell
```

### Step 2: Add RFP Document

Add your RFP document to the `/memory/` directory:

```bash
cp ~/Downloads/rfp.pdf memory/rfp-document.md
# or create it manually
touch memory/rfp-document.md
```

### Step 3: Analyze the RFP

**In your AI Agent's chat interface**, use the `/rfpkit.analyze` slash command to extract requirements, deadlines, and evaluation criteria:

```markdown
/rfpkit.analyze
```

### Step 4: Create Guidelines

**In the chat**, use the `/rfpkit.guidelines` slash command to create structured guidelines for your proposal:

```markdown
/rfpkit.guidelines
```

### Step 5: Develop Win Strategy

**In the chat**, use the `/rfpkit.strategy` slash command to create win themes and competitive positioning:

```markdown
/rfpkit.strategy Focus on our DDI transformation expertise, multi-cloud mastery, and federal experience. Emphasize zero-downtime migrations.
```

### Step 6: Draft Proposal Sections

**In the chat**, draft individual sections using `/rfpkit.section`:

```markdown
/rfpkit.section Technical Approach - Deliverable 1: Network Assessment
```

Repeat for all required sections:

```markdown
/rfpkit.section Executive Summary
/rfpkit.section Past Performance
/rfpkit.section Project Management Approach
/rfpkit.section Cost Volume
```

### Step 7: Run Compliance Check

**In the chat**, verify compliance using `/rfpkit.compliance`:

```markdown
/rfpkit.compliance
```

Address any identified gaps and re-run compliance until you achieve 98%+ coverage.

## Detailed Example: DNS/Cloud Assessment RFP

Here's a complete example of responding to a federal RFP:

### Step 1: Initialize Project

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init dns-cloud-rfp --ai copilot
```

### Step 2: Add RFP Document

Copy the RFP to `/memory/rfp-document.md` with all requirements, evaluation criteria, and deadlines.

### Step 3: Analyze with `/rfpkit.analyze`

```text
/rfpkit.analyze
```

This extracts:
- 57 technical requirements
- 4 evaluation criteria (Technical: 40pts, Past Performance: 30pts, Management: 20pts, Cost: 10pts)
- Submission deadline: March 15, 2026
- Estimated value: $1.8-2.5M

### Step 4: Create Guidelines

```text
/rfpkit.guidelines
```

This creates structured writing standards, evidence requirements, and compliance checklist.

### Step 5: Develop Win Strategy

```text
/rfpkit.strategy Focus on DDI transformation expertise (15+ federal migrations), multi-cloud mastery (AWS/Azure/GCP), Cisco ACI experience, and M&A integration capabilities. Emphasize zero-downtime track record and 99.99% uptime.
```

This creates:
- 4 win themes with proof points
- Competitive positioning matrix
- Risk mitigation strategies
- Case study library

### Step 6: Draft Sections

Draft all 8 sections:

```text
/rfpkit.section Executive Summary
/rfpkit.section Deliverable 1: Assessment Approach
/rfpkit.section Deliverable 2: Design Approach
/rfpkit.section Deliverable 3: Migration Approach
/rfpkit.section Deliverable 4: Operations Approach
/rfpkit.section Past Performance
/rfpkit.section Project Management
/rfpkit.section Cost Volume
```

Each section includes:
- Win theme integration
- Evidence and proof points
- Requirement-by-requirement compliance
- Scoring optimization

### Step 7: Verify Compliance

```text
/rfpkit.compliance
```

Results:
- **56 of 57 requirements addressed** (98.2% compliance)
- 1 medium-risk gap identified (pricing format)
- Recommendations provided

Address the gap:

```text
Update the Cost Volume section to add a detailed pricing table showing cost breakdown by deliverable.
```

Re-run compliance:

```text
/rfpkit.compliance
```

Final result: **100% compliance**

## Key Principles

- **Analyze first** - Understand all requirements before writing
- **Strategy early** - Develop win themes and positioning upfront
- **Evidence always** - Support every claim with proof points
- **Compliance throughout** - Track requirements from start to finish
- **Iterate and validate** - Use compliance checks to verify coverage

## Real-World Results

Using this workflow, RFP Kit users have generated:

- **8-section proposals** (~60-80 pages)
- **98.2% compliance** (56 of 57 requirements)
- **Complete in days** instead of weeks
- **$2.1M cost volumes** with detailed justification
- **4 detailed case studies** with metrics

## Next Steps

- Explore the [installation guide](installation.md) for detailed setup
- Check out [supported AI agents](https://github.com/sketabchi/rfpkit#-supported-ai-agents)
- View the [source code on GitHub](https://github.com/sketabchi/rfpkit)
