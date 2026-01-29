---
description: Analyze RFP document to extract key requirements, evaluation criteria, deadlines, and compliance items.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Analyze the RFP document(s) in `/memory/` to extract and structure critical information including:
- RFP overview (agency, title, solicitation number)
- Key dates and deadlines
- Page limits and formatting requirements
- Evaluation criteria and scoring methodology
- Must-have requirements and compliance items
- Technical requirements and specifications
- Submission instructions

## Operating Constraints

**READ-ONLY ANALYSIS**: Do not modify existing files. Output a structured analysis report that can be used to create `/memory/guidelines.md` via `/rfpkit.guidelines`.

**Document Sources**: Analyze RFP documents from `/memory/` directory. Look for files like:
- `rfp-document.md` or `rfp-document.pdf`
- `solicitation.md` or `solicitation.pdf`
- Any other RFP-related documents the user specifies

## Execution Steps

### 1. Locate RFP Documents

Search the `/memory/` directory for RFP documents. If user specified a document name in arguments, use that. Otherwise, look for common patterns:
- Files containing "rfp", "solicitation", "request for proposal"
- Markdown (.md) or PDF (.pdf) files in `/memory/`

If no documents found, ask user to provide the RFP document location.

### 2. Extract RFP Metadata

Analyze the document to identify:

**RFP Overview:**
- Issuing agency/organization
- RFP title
- Solicitation/RFP number
- Contract type (FFP, T&M, CPFF, etc.)
- Contract value estimate (if provided)

**Critical Dates:**
- RFP release date
- Questions/clarifications deadline
- Proposal due date/time (note timezone!)
- Anticipated award date
- Period of performance (base + option years)

**Submission Requirements:**
- Page limits (by section/volume)
- Format requirements (font, margins, spacing)
- Number of copies required
- Electronic vs paper submission
- Submission location/portal

### 3. Extract Evaluation Criteria

Identify how proposals will be evaluated:

**Evaluation Methodology:**
- LPTA (Lowest Price Technically Acceptable)
- Best Value Tradeoff
- Other methodology

**Evaluation Factors:**
- Technical approach/solution (weight/points)
- Past performance (weight/points)
- Management approach (weight/points)
- Price/cost (weight/points)
- Other factors

**Scoring Details:**
- Point values for each factor
- Sub-criteria and scoring rubrics
- Adjectival ratings (Exceptional, Good, Acceptable, etc.)

### 4. Extract Requirements

**Must-Have Requirements (Go/No-Go):**
- Mandatory qualifications
- Required certifications
- Minimum experience requirements
- Mandatory technical specifications

**Technical Requirements:**
- Functional requirements
- Performance requirements
- Technical specifications
- Standards and compliance needs
- Security requirements
- Integration requirements

**Deliverables:**
- Required deliverables
- Delivery schedules
- Acceptance criteria

### 5. Identify Compliance Items

**Representations and Certifications:**
- Required forms (SF-30, SF-1449, etc.)
- Certifications needed
- Bonding requirements

**Small Business Requirements:**
- Set-aside type (8(a), SDVOSB, HUBZone, etc.)
- Subcontracting plan requirements
- DBE/MBE goals

### 6. Produce RFP Analysis Report

Output a comprehensive Markdown report with:

## RFP Analysis Report

### Executive Summary
- RFP Title
- Issuing Agency
- Solicitation Number
- Proposal Due Date
- Contract Value
- Evaluation Methodology

### Critical Dates
| Event | Date/Time | Notes |
|-------|-----------|-------|
| Questions Deadline | [date] | [timezone] |
| Proposal Due | [date] | [hard deadline] |
| Anticipated Award | [date] | |

### Proposal Requirements
| Section/Volume | Page Limit | Format Requirements |
|----------------|------------|---------------------|
| Technical Volume | XX pages | [font, margins] |
| Management Volume | XX pages | |
| Past Performance | XX pages | |
| Cost Volume | XX pages | |

### Evaluation Criteria
| Factor | Weight/Points | Sub-Criteria |
|--------|---------------|--------------|
| Technical Approach | XX points | [list sub-criteria] |
| Management | XX points | |
| Past Performance | XX points | |
| Price | XX points | |

### Must-Have Requirements (Compliance Matrix)
| Requirement | Location in RFP | Compliance Status | Response Plan |
|-------------|-----------------|-------------------|---------------|
| [Must-have item] | Section X.X | [ ] To Address | |

### Technical Requirements Summary
- **Functional**: [List key functional requirements]
- **Performance**: [List performance requirements]
- **Security**: [List security requirements]
- **Integration**: [List integration requirements]

### Deliverables Schedule
| Deliverable | Due Date | Acceptance Criteria |
|-------------|----------|---------------------|

### Risk Assessment
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Tight deadline | HIGH | HIGH | [strategy] |
| Page limits | MED | MED | [strategy] |

### Next Steps
1. **Immediate**: Run `/rfpkit.guidelines` to create structured guidelines document
2. **Strategy**: Run `/rfpkit.strategy` to develop win strategy
3. **Compliance**: Run `/rfpkit.compliance` to verify requirement coverage
4. **Competitive**: Run `/rfpkit.competitive` to analyze competitive landscape

---

**Analysis Complete!** This RFP analysis provides the foundation for your proposal development. Next, use `/rfpkit.guidelines` to convert this analysis into a structured guidelines document that will guide all proposal content.
