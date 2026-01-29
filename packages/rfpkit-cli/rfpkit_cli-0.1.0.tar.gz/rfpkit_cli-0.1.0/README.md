<div align="center">
    <h1>📋 RFP Kit</h1>
    <h3><em>Win more proposals with AI-powered response development.</em></h3>
</div>

<p align="center">
    <strong>A structured framework for developing high-quality RFP responses using AI agents. Transform complex RFPs into winning proposals with systematic analysis, strategy, and content generation.</strong>
</p>

<p align="center">
    <a href="https://github.com/sketabchi/rfpkit/actions/workflows/release.yml"><img src="https://github.com/sketabchi/rfpkit/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/sketabchi/rfpkit/stargazers"><img src="https://img.shields.io/github/stars/sketabchi/rfpkit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/sketabchi/rfpkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/sketabchi/rfpkit" alt="License"/></a>
</p>

---

## Table of Contents

- [🤔 What is RFP Kit?](#-what-is-rfp-kit)
- [⚡ Get Started](#-get-started)
- [🎯 Real-World Results](#-real-world-results)
- [🤖 Supported AI Agents](#-supported-ai-agents)
- [🔧 RFP Kit CLI Reference](#-rfp-kit-cli-reference)
- [📚 Core Methodology](#-core-methodology)
- [🌟 RFP Response Phases](#-rfp-response-phases)
- [💡 Key Features](#-key-features)
- [🔧 Prerequisites](#-prerequisites)
- [📖 Learn More](#-learn-more)
- [👥 Maintainers](#-maintainers)
- [💬 Support](#-support)
- [📄 License](#-license)

## 🤔 What is RFP Kit?

RFP Kit transforms the RFP response process from chaotic firefighting into a **systematic, AI-powered workflow**. Instead of scrambling to respond to RFPs with generic content, RFP Kit helps you:

- **Analyze RFPs systematically** - Extract requirements, deadlines, and evaluation criteria automatically
- **Develop winning strategies** - Create competitive positioning and win themes backed by evidence
- **Generate compliant content** - Draft proposal sections that map to evaluation criteria with proof points
- **Verify compliance** - Ensure 98%+ compliance before submission with automated checking
- **Optimize for scoring** - Structure content to maximize evaluation points

**Real-world validated**: Generated a 60-80 page proposal with 98.2% compliance in days, not weeks.

## ⚡ Get Started

### 1. Install RFP Kit CLI

Choose your preferred installation method:

#### Option 1: Persistent Installation (Recommended)

Install once and use everywhere:

```bash
uv tool install rfpkit-cli --from git+https://github.com/sketabchi/rfpkit.git
```

Then use the tool directly:

```bash
# Create new RFP response project
rfpkit init my-rfp-project

# Or initialize in existing directory
rfpkit init . --ai copilot
# or
rfpkit init --here --ai copilot

# Check installed tools
rfpkit check
```

To upgrade RFP Kit:

```bash
uv tool install rfpkit-cli --force --from git+https://github.com/sketabchi/rfpkit.git
```

#### Option 2: One-time Usage

Run directly without installing:

```bash
uvx --from git+https://github.com/sketabchi/rfpkit.git rfpkit init my-rfp-project
```

**Benefits of persistent installation:**

- Tool stays installed and available in PATH
- No need to create shell aliases
- Better tool management with `uv tool list`, `uv tool upgrade`, `uv tool uninstall`
- Cleaner shell configuration

### 2. Add Your RFP Document

Place your RFP document in the `/memory/` folder:

```bash
# Copy your RFP to the memory folder
cp ~/Downloads/RFP-Document.pdf memory/rfp-document.pdf
# or if you have it in Markdown
cp ~/Downloads/RFP.md memory/rfp-document.md
```

### 3. Analyze the RFP

Use **`/rfpkit.analyze`** to extract requirements, deadlines, and evaluation criteria:

```bash
/rfpkit.analyze
```

This generates a comprehensive RFP analysis report including:
- Critical dates and deadlines
- Evaluation criteria and scoring
- Must-have requirements
- Technical specifications
- Deliverables and compliance items

### 4. Create Guidelines

Use **`/rfpkit.guidelines`** to convert the analysis into structured guidelines:

```bash
/rfpkit.guidelines
```

This creates `/memory/guidelines.md` with:
- RFP requirements matrix
- Evaluation criteria breakdown
- Compliance checklist
- Page limits and format requirements

### 5. Develop Win Strategy

Use **`/rfpkit.strategy`** to create your competitive strategy:

```bash
/rfpkit.strategy
```

This generates `/memory/strategy.md` with:
- Win themes with proof points
- Competitive analysis
- Differentiation strategy
- Solution architecture overview
- Proof points library

### 6. Draft Proposal Sections

Use **`/rfpkit.section`** to create each proposal section:

```bash
/rfpkit.section Technical Approach
/rfpkit.section Past Performance
/rfpkit.section Management Plan
/rfpkit.section Cost Volume
```

Each section includes:
- Requirements tracking
- Evidence and proof points
- Evaluation scoring strategy
- Win theme integration
- Quality checklist

### 7. Run Compliance Check

Use **`/rfpkit.compliance`** to verify requirement coverage:

```bash
/rfpkit.compliance
```

This generates a compliance report showing:
- Overall compliance rate (target: 98%+)
- High/medium/low risk gaps
- Missing requirements
- Recommendations for improvement

### 8. Final Review

Use **`/rfpkit.checklist`** for final quality verification before submission.

## 🎯 Real-World Results

**Test Case**: DNS and Cloud Network Assessment RFP

**Generated Output**:
- **8 comprehensive sections** (~60-80 pages)
- **98.2% compliance rate** (56 of 57 requirements fully addressed)
- **$2.1M cost volume** with transparent deliverable-based pricing
- **4 detailed case studies** with metrics and proof points
- **Complete in days**, not weeks

**Sections Created**:
1. Executive Summary (3-5 pages)
2. Technical Approach - 4 Deliverables (8-10 pages each)
3. Past Performance (15-20 pages)
4. Project Management (5-6 pages)
5. Cost Volume (8-12 pages)

**Compliance Highlights**:
- ✅ 100% technical requirements addressed
- ✅ 100% evaluation criteria covered with evidence
- ✅ All deliverables fully scoped
- ✅ Complete project management framework
- ✅ Transparent, competitive pricing

## 🤖 Supported AI Agents

RFP Kit works with all major AI coding assistants:

| Agent                                                                                | Support | Notes                                                                                                                                     |
| ------------------------------------------------------------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | ✅      | Recommended - Tested with real-world RFP                                                                                                |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | ✅      |                                                                                                                                           |
| [Cursor](https://cursor.sh/)                                                         | ✅      |                                                                                                                                           |
| [Windsurf](https://windsurf.com/)                                                    | ✅      |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | ✅      |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | ✅      |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | ✅      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | ✅      |                                                                                                                                           |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | ✅      |                                                                                                                                           |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | ✅      |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | ✅      |                                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | ✅      |                                                                                                                                           |
| [Qoder CLI](https://qoder.com/cli)                                                   | ✅      |                                                                                                                                           |
| [Amp](https://ampcode.com/)                                                          | ✅      |                                                                                                                                           |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | ✅      |                                                                                                                                           |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | ✅      | IDE-based agent with slash command support                                                                                                |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️      | Amazon Q Developer CLI [does not support](https://github.com/aws/amazon-q-developer-cli/issues/3064) custom arguments for slash commands. |

## 🔧 RFP Kit CLI Reference

The `rfpkit` command supports the following options:

### Commands

| Command | Description                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init`  | Initialize a new RFP response project from the latest template                                                                                          |
| `check` | Check for installed tools (`git`, `claude`, `gemini`, `code`/`code-insiders`, `cursor-agent`, `windsurf`, `qwen`, `opencode`, `codex`, `shai`, `qoder`) |

### `rfpkit init` Arguments & Options

| Argument/Option        | Type     | Description                                                                                                                                                                                  |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<project-name>`       | Argument | Name for your new project directory (optional if using `--here`, or use `.` for current directory)                                                                                           |
| `--ai`                 | Option   | AI assistant to use: `claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, `shai`, `q`, `bob`, or `qoder` |
| `--script`             | Option   | Script variant to use: `sh` (bash/zsh) or `ps` (PowerShell)                                                                                                                                  |
| `--ignore-agent-tools` | Flag     | Skip checks for AI agent tools like Claude Code                                                                                                                                              |
| `--no-git`             | Flag     | Skip git repository initialization                                                                                                                                                           |
| `--here`               | Flag     | Initialize project in the current directory instead of creating a new one                                                                                                                    |
| `--force`              | Flag     | Force merge/overwrite when initializing in current directory (skip confirmation)                                                                                                             |
| `--skip-tls`           | Flag     | Skip SSL/TLS verification (not recommended)                                                                                                                                                  |
| `--debug`              | Flag     | Enable detailed debug output for troubleshooting                                                                                                                                             |
| `--github-token`       | Option   | GitHub token for API requests (or set GH_TOKEN/GITHUB_TOKEN env variable)                                                                                                                    |

### Examples

```bash
# Basic project initialization
rfpkit init my-rfp-response

# Initialize with GitHub Copilot
rfpkit init my-rfp-response --ai copilot

# Initialize with Claude Code
rfpkit init my-rfp-response --ai claude

# Initialize with Cursor support
rfpkit init my-rfp-response --ai cursor-agent

# Initialize with PowerShell scripts (Windows/cross-platform)
rfpkit init my-rfp-response --ai copilot --script ps

# Initialize in current directory
rfpkit init . --ai copilot
# or use the --here flag
rfpkit init --here --ai copilot

# Force merge into current (non-empty) directory without confirmation
rfpkit init . --force --ai copilot

# Skip git initialization
rfpkit init my-rfp-response --ai gemini --no-git

# Enable debug output for troubleshooting
rfpkit init my-rfp-response --ai claude --debug

# Check system requirements
rfpkit check
```

### Available Slash Commands

After running `rfpkit init`, your AI coding agent will have access to these slash commands for structured RFP response development:

#### Core RFP Commands

Essential commands for the RFP response workflow:

| Command                | Description                                                                     |
| ---------------------- | ------------------------------------------------------------------------------- |
| `/rfpkit.analyze`      | Analyze RFP document to extract requirements, deadlines, and evaluation criteria |
| `/rfpkit.guidelines`   | Create structured guidelines document from RFP analysis                         |
| `/rfpkit.strategy`     | Develop win strategy with themes, competitive positioning, and proof points     |
| `/rfpkit.tasks`        | Generate task breakdown for proposal development                                |
| `/rfpkit.section`      | Draft individual proposal sections with evidence and scoring strategy           |
| `/rfpkit.draft`        | Assemble complete proposal from all sections                                    |

#### Quality & Compliance Commands

Additional commands for validation and optimization:

| Command                | Description                                                                     |
| ---------------------- | ------------------------------------------------------------------------------- |
| `/rfpkit.compliance`   | Verify requirement coverage and generate compliance report                      |
| `/rfpkit.competitive`  | Analyze competitive landscape and create positioning strategy                   |
| `/rfpkit.pricing`      | Draft cost volume with pricing strategy and justification                       |
| `/rfpkit.checklist`    | Generate quality checklist for final review                                     |
| `/rfpkit.clarify`      | Clarify underspecified areas or ambiguous requirements                          |

## 📚 Core Methodology

RFP Kit follows a structured approach to RFP response development:

- **Analysis-driven** - Extract and structure RFP requirements before writing
- **Strategy-first** - Develop win themes and competitive positioning early
- **Evidence-based** - Every claim supported by metrics, case studies, and proof points
- **Compliance-focused** - Track requirements throughout the process
- **Evaluation-optimized** - Structure content to maximize scoring potential

## 🌟 RFP Response Phases

| Phase                           | Focus                     | Key Activities                                                                                                                                                     |
| ------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Analysis & Strategy**         | Understand & Position     | <ul><li>Analyze RFP requirements</li><li>Extract evaluation criteria</li><li>Develop win strategy</li><li>Create competitive positioning</li></ul>                |
| **Content Development**         | Draft Proposal Sections   | <ul><li>Draft technical approach</li><li>Create past performance</li><li>Develop management plan</li><li>Build cost volume</li></ul>                              |
| **Quality & Compliance**        | Verify & Optimize         | <ul><li>Run compliance check</li><li>Verify requirement coverage</li><li>Optimize for scoring</li><li>Final quality review</li></ul>                              |

## 💡 Key Features

### Systematic RFP Analysis

- Automatic extraction of requirements, deadlines, and evaluation criteria
- Compliance matrix generation
- Risk assessment and gap identification

### Strategic Win Positioning

- Win theme development with proof points
- Competitive analysis and differentiation
- Solution architecture alignment

### Evidence-Based Content

- Case study templates with metrics
- Proof points library
- Competitive messaging guides

### Compliance Verification

- Automated requirement tracking
- 98%+ compliance validation
- Gap analysis and recommendations

### Evaluation Optimization

- Content-to-scoring-criteria mapping
- High/medium/low value content identification
- Competitive benchmarking
- Validate the hypothesis that Spec-Driven Development is a process not tied to specific technologies, programming languages, or frameworks

### Enterprise constraints

- Demonstrate mission-critical application development
- Incorporate organizational constraints (cloud providers, tech stacks, engineering practices)
- Support enterprise design systems and compliance requirements

### User-centric development

- Build applications for different user cohorts and preferences
- Support various development approaches (from vibe-coding to AI-native development)

### Creative & iterative processes

- Validate the concept of parallel implementation exploration
- Provide robust iterative feature development workflows
- Extend processes to handle upgrades and modernization tasks

## 🔧 Prerequisites

- **Linux/macOS/Windows**
- [Supported](#-supported-ai-agents) AI coding agent.
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter issues with an agent, please open an issue so we can refine the integration.

## 📖 Learn More

- **[RFP Response Workflow Guide](#-detailed-process)** - Step-by-step walkthrough of the complete process
- **[Real-World Case Study](#-get-started)** - See actual results from DNS/Cloud Assessment RFP

---

## 📋 Detailed Process

<details>
<summary>Click to expand the detailed step-by-step walkthrough</summary>

You can use the RFP Kit CLI to bootstrap your project, which will bring in the required templates and structure. Run:

```bash
rfpkit init <project_name>
```

Or initialize in the current directory:

```bash
rfpkit init .
# or use the --here flag
rfpkit init --here
# Skip confirmation when the directory already has files
rfpkit init . --force
# or
rfpkit init --here --force
```

You will be prompted to select the AI agent you are using. You can also proactively specify it directly in the terminal:

```bash
rfpkit init <project_name> --ai copilot
rfpkit init <project_name> --ai claude
rfpkit init <project_name> --ai gemini

# Or in current directory:
rfpkit init . --ai copilot
rfpkit init . --ai cursor-agent

# or use --here flag
rfpkit init --here --ai copilot
rfpkit init --here --ai claude

# Force merge into a non-empty current directory
rfpkit init . --force --ai copilot

# or
rfpkit init --here --force --ai copilot
```

The CLI will check if you have the required AI agent tools installed. If you prefer to get the templates without checking for tools, use `--ignore-agent-tools`:

```bash
rfpkit init <project_name> --ai copilot --ignore-agent-tools
```

### **STEP 1:** Add RFP Document

Go to the project folder and run your AI agent. In our example, we're using GitHub Copilot.

You will know that things are configured correctly if you see the `/rfpkit.analyze`, `/rfpkit.guidelines`, `/rfpkit.strategy`, `/rfpkit.section`, and other RFP Kit commands available.

The first step is to add your RFP document to the `/memory/` directory. You can name it `rfp-document.md` or any descriptive name:

```bash
# Copy your RFP PDF/Word document content to markdown
cp ~/Downloads/rfp.pdf memory/rfp-document.md
# or create it manually
touch memory/rfp-document.md
```

Ensure the RFP document includes:
- Requirements and deliverables
- Evaluation criteria and scoring
- Submission deadlines
- Background information
- Statement of Work (SOW)

### **STEP 2:** Analyze RFP Document

With your RFP document in place, analyze it to extract requirements and metadata. Use the `/rfpkit.analyze` command:

```text
/rfpkit.analyze
```

This command will:
- Extract all requirements and deliverables
- Identify evaluation criteria and scoring weights
- Parse submission deadlines and milestones
- Analyze background information and context
- Generate a structured RFP analysis report

> [!IMPORTANT]
> The analysis output helps you understand what the customer values and how your proposal will be evaluated. Review it carefully before proceeding.

Example analysis output structure:

```text
# RFP Analysis

## Executive Summary
- RFP Title: DNS and Cloud Network Assessment
- Issuing Organization: Federal Agency XYZ
- Due Date: March 15, 2026
- Estimated Contract Value: $1.8-2.5M

## Requirements Breakdown
1. Technical Requirements (45 items)
2. Management Requirements (12 items)
3. Deliverable Requirements (8 items)

## Evaluation Criteria
- Technical Approach: 40 points
- Past Performance: 30 points
- Management: 20 points
- Cost: 10 points
```

At this stage, your project folder should contain:

```text
├── memory/
│   ├── rfp-document.md
│   └── rfp-analysis.md (generated)
├── sections/ (empty, ready for proposal sections)
└── templates/ (RFP Kit templates)
```

### **STEP 3:** Create Guidelines Document

With the RFP analyzed, create structured guidelines to inform all proposal sections. Use the `/rfpkit.guidelines` command:

```text
/rfpkit.guidelines
```

This creates `/memory/guidelines.md` with:

1. **Writing Standards** - Tone, style, terminology preferences
2. **Compliance Requirements** - Must-have elements for each section
3. **Evidence Standards** - How to present metrics, case studies, proof points
4. **Formatting Guidelines** - Page limits, fonts, structure requirements
5. **Evaluation Mapping** - How content maps to scoring criteria

You can refine the guidelines with follow-up prompts:

```text
Add a section about how to present cloud migration experience, emphasizing our 15+ federal agency migrations and zero-downtime track record.
```

Example guidelines structure:

```text
# Proposal Guidelines

## Writing Standards
- Use active voice and action verbs
- Lead with benefits, then explain features
- Address evaluation criteria explicitly

## Evidence Standards  
- Every capability claim needs proof point
- Metrics must include: baseline, outcome, timeframe
- Case studies: 3-5 paragraphs with problem-solution-results

## Compliance Checklist
- [ ] Address all technical requirements
- [ ] Include required certifications
- [ ] Meet page limits per section
```

> [!IMPORTANT]
> The guidelines document serves as the foundation for all sections. Invest time to make it comprehensive and aligned with the RFP's evaluation criteria.

### **STEP 4:** Develop Win Strategy

Create your competitive positioning and win themes using the `/rfpkit.strategy` command:

```text
/rfpkit.strategy Focus on our DDI transformation expertise, multi-cloud mastery, Cisco ACI experience, and M&A integration capabilities. Emphasize federal experience and zero-downtime migrations.
```

This creates `/memory/strategy.md` with:

1. **Win Themes** - 3-5 core messages that differentiate your solution
2. **Competitive Analysis** - SWOT analysis and positioning matrix
3. **Proof Points Library** - Case studies, metrics, and evidence
4. **Risk Mitigation** - How you address customer concerns
5. **Value Proposition** - Why you're the best choice

Example win strategy structure:

```text
# Win Strategy

## Executive Summary
- Win Probability: 75% (High)
- Key Differentiators: Federal DDI expertise, Zero-downtime track record
- Primary Competitor: Competitor X (lacks federal experience)

## Win Themes

### Theme 1: DDI Transformation Excellence
- **Message**: Proven expertise in modernizing DNS/DHCP/IPAM
- **Proof Point**: 15+ federal agency DDI migrations
- **Evidence**: Average 40% cost reduction, 99.99% uptime

### Theme 2: Multi-Cloud Mastery  
- **Message**: Seamless integration across AWS, Azure, GCP
- **Proof Point**: $50M+ multi-cloud programs delivered
- **Evidence**: Zero security incidents, 100% compliance

## Competitive Positioning Matrix
| Criteria | Us | Competitor X | Competitor Y |
|----------|-----|--------------|-------------|
| Federal Experience | Strong | Weak | Medium |
| DDI Expertise | Strong | Medium | Medium |
| Cost | Competitive | Higher | Lower |
```

You can refine with follow-up prompts:

```text
Add a proof point about our recent VA migration project - 250k endpoints, completed 2 months early, zero downtime.
```

### **STEP 5:** Draft Proposal Sections

With strategy in place, draft individual proposal sections using the `/rfpkit.section` command:

```text
/rfpkit.section Technical Approach - Deliverable 1: Network Assessment
```

This creates a file in `/sections/` (e.g., `technical-approach-deliverable-1.md`) with:

1. **Section Overview** - Page limits, scoring weight, key requirements
2. **Content Strategy** - Win theme integration, evidence placement
3. **Structured Content** - Executive summary, approach, differentiators
4. **Compliance Tracking** - Requirement-by-requirement verification
5. **Quality Checklist** - Pre-submission validation items

Repeat for all required sections:

```text
/rfpkit.section Executive Summary
/rfpkit.section Past Performance
/rfpkit.section Project Management Approach  
/rfpkit.section Cost Volume
```

Example section structure:

```text
# Technical Approach - Deliverable 1: Network Assessment

## Section Overview
- **Page Limit**: 8-10 pages
- **Scoring Weight**: 40 points (highest)
- **Key Requirements**: 12 technical requirements to address

## Executive Summary
[3-paragraph overview highlighting win themes]

## Approach
### Phase 1: Discovery and Baseline Assessment
[Detailed methodology with proof points]

### Phase 2: Analysis and Recommendations
[Technical approach with case study]

## Differentiators
- **DDI Transformation Expertise**: 15+ federal migrations
- **Zero-Downtime Track Record**: 99.99% uptime
```

Refine sections with specific guidance:

```text
Add a detailed case study about the VA migration in the Past Performance section. Include metrics: 250k endpoints, 2 months early, $1.2M cost savings.
```

### **STEP 6:** Run Compliance Check

Before finalizing, verify that all RFP requirements are addressed using the `/rfpkit.compliance` command:

```text
/rfpkit.compliance
```

This generates a comprehensive compliance report that:

- **Requirement Verification** - Checks all 57 RFP requirements against your sections
- **Coverage Analysis** - Identifies addressed vs. missing requirements
- **Gap Identification** - Highlights High/Medium/Low risk gaps
- **Recommendations** - Provides specific guidance to close gaps
- **Compliance Score** - Overall percentage (target: 98%+)

Example compliance report output:

```text
# Compliance Report

## Executive Summary
- **Total Requirements**: 57
- **Addressed**: 56 (98.2%)
- **Gaps Identified**: 1 (Medium Risk)
- **Recommendation**: Address pricing format gap before submission

## Requirements Matrix
| Requirement | Section | Status | Gap Risk |
|------------|---------|--------|----------|
| R-1: Network assessment methodology | Technical Approach | ✅ Addressed | - |
| R-2: Multi-cloud integration | Technical Approach | ✅ Addressed | - |
| R-57: Pricing breakdown by deliverable | Cost Volume | ⚠️ Partial | Medium |

## Gap Analysis
### Medium Risk Gaps (1)
- **R-57**: Pricing format needs deliverable-based breakdown table
  - Current: Narrative description of costs  
  - Required: Table with per-deliverable pricing
  - Recommendation: Add pricing table to Cost Volume section
```

Address identified gaps:

```text
Update the Cost Volume section to add a detailed pricing table showing cost breakdown by deliverable, as identified in the compliance report.
```

### **STEP 7:** Final Review and Assembly

Once all gaps are closed, perform final quality review:

1. **Run Final Compliance Check**
   ```text
   /rfpkit.compliance
   ```
   - Target: 100% requirement coverage
   - Verify all High and Medium risk gaps resolved

2. **Quality Review Checklist**
   ```text
   /rfpkit.checklist
   ```
   - Generates section-by-section quality validation
   - Checks: Page limits, formatting, evidence, tone

3. **Assemble Final Proposal** (Optional)
   ```text
   /rfpkit.draft
   ```
   - Combines all sections into single document
   - Adds table of contents, page numbers
   - Ensures consistent formatting

4. **Final Polish**
   - Executive summary aligns with all sections
   - Win themes are consistently woven throughout
   - Evidence and proof points are up-to-date
   - Page limits are met
   - All requirements explicitly addressed

> [!TIP]
> **Real-World Results**: Using this workflow, we generated an 8-section proposal (60-80 pages) for a DNS/Cloud Assessment RFP with 98.2% compliance (56 of 57 requirements) in days instead of weeks. The proposal included: Executive Summary, 4 Technical Deliverable sections, Past Performance with case studies, Project Management Plan, and Cost Volume with $2.1M pricing.

</details>

---

## 🔍 Troubleshooting

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

## 👥 Maintainers

- Shahrokh Ektabchi ([@sketabchi](https://github.com/sketabchi))

## 💬 Support

For support, please open a [GitHub issue](https://github.com/sketabchi/rfpkit/issues/new). We welcome bug reports, feature requests, and questions about using RFP Kit.

## 🙏 Acknowledgements

This project is built upon the Spec Kit framework, originally developed by [John Lam](https://github.com/jflam) and [Den Delimarsky](https://github.com/localden).

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
