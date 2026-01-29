---
description: Draft an RFP proposal section with evidence, scoring strategy, and compliance mapping.
---

# RFP Section Drafter

## User Input

```text
$ARGUMENTS
```

## Instructions

Create a comprehensive RFP proposal section based on the user's description. Write directly to `/sections/[section-name].md` without any branching or spec.md files.

### Step 1: Parse User Request

Extract from the user's input:
- Section name (e.g., "Technical Approach", "Deliverable 1 - Assessment Phase")
- Key requirements to address
- Any specific page limit or guidance

### Step 2: Generate Filename

Convert section name to filename:
- Lowercase, hyphens instead of spaces
- Example: "Technical Approach" → `technical-approach.md`
- Example: "Deliverable 1: Assessment" → `deliverable-1-assessment.md`

### Step 3: Create Sections Directory

Ensure `/sections/` directory exists in the project root.

### Step 4: Load Reference Documents

If available, load:
- `/memory/guidelines.md` - RFP requirements and evaluation criteria
- `/memory/strategy.md` - Win themes and competitive positioning  
- `/section-template.md` - Template structure

### Step 5: Draft Section Content

Using the section-template.md structure, create comprehensive content with:

**Section Overview:**
- Page limit and point value
- Requirements tracking table
- Compliance summary

**Content Strategy:**
- Key messages with P1/P2/P3 priorities
- Evidence (case studies, metrics, proof points)
- Evaluation criteria mapping
- Page allocations
- Competitive differentiation

**Evaluation Scoring Strategy:**
- Scoring criteria breakdown
- Content-to-score mapping
- Target score and competitive benchmark

**Section Structure:**
- Detailed outline with page allocations
- Win theme integration throughout

**Quality Checklist:**
- Compliance verification
- Content quality checks
- Scoring optimization

### Step 6: Write File

Write the complete section to `/sections/[filename].md` with frontmatter:

```markdown
# RFP Section: [Section Name]

**RFP Reference**: [RFP Title]
**Section Number**: [Section identifier]  
**Created**: [Today's date]
**Status**: Draft

[...full section content following template structure...]
```

### Step 7: Report Completion

Confirm:
- ✅ File location: `/sections/[filename].md`
- 📄 Estimated page count
- 🎯 Next actions: Review content, run compliance check, create additional sections

## Content Standards

- **Evidence-based**: Every claim supported by metrics, case studies, or proof points
- **Scannable**: Clear headers, bullet lists, tables
- **Customer-focused**: Benefits over features
- **Win theme integration**: Weave themes throughout
- **Evaluation-optimized**: Structure for maximum scoring

---

**No branching. No specs/ folder. Direct file creation in /sections/ only.**
      
      ## Requirement Completeness
      
      - [ ] No [NEEDS CLARIFICATION] markers remain
      - [ ] Requirements are testable and unambiguous
      - [ ] Success criteria are measurable
      - [ ] Success criteria are technology-agnostic (no implementation details)
      - [ ] All acceptance scenarios are defined
      - [ ] Edge cases are identified
      - [ ] Scope is clearly bounded
      - [ ] Dependencies and assumptions identified
      
      ## Feature Readiness
      
      - [ ] All functional requirements have clear acceptance criteria
      - [ ] User scenarios cover primary flows
      - [ ] Feature meets measurable outcomes defined in Success Criteria
      - [ ] No implementation details leak into specification
      
      ## Notes
      
      - Items marked incomplete require spec updates before `/rfpkit.clarify` or `/rfpkit.plan`
      ```

   b. **Run Validation Check**: Review the spec against each checklist item:
      - For each item, determine if it passes or fails
      - Document specific issues found (quote relevant spec sections)

   c. **Handle Validation Results**:

      - **If all items pass**: Mark checklist complete and proceed to step 6

      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues
        2. Update the spec to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
- Page limit and point value for this section
- Requirements tracking table (map RFP requirements to section content)
- Compliance summary

**Content Strategy:**
- Key messages prioritized (P1, P2, P3)
- Each message mapped to evaluation criteria
- Supporting evidence (case studies, metrics, proof points)
- Page allocation by priority
- Differentiation points vs competitors

**Evaluation Scoring Strategy:**
- Scoring criteria breakdown with weights
- Content-to-score mapping (high/medium/low value content)
- Target score and competitive benchmark
- Risk assessment and mitigation

**Section Structure:**
- Detailed outline with page allocations
- Win theme integration
- Visual strategy (required graphics)

**Quality Checklist:**
- Compliance review items
- Content quality validation
- Scoring optimization checks
- Production readiness items

### 5. Write Section File

Create the section file at `/sections/[filename].md` with:

**Frontmatter:**
```markdown
# RFP Section: [Section Name]

**RFP Reference**: [RFP Title]
**Section Number**: [Section number/identifier]
**Created**: [Date]
**Status**: Draft
**Input**: "[User's original request]"
```

**Full content following template structure** with all sections populated based on available context from guidelines, strategy, and user requirements.

### 6. Create Sections Directory if Needed

If `/sections/` directory doesn't exist, create it first before writing the section file.

### 7. Report Completion

After creating the section, provide:
- ✅ Section file location (`/sections/[filename].md`)
- 📄 Page count estimate (based on content generated)
- 🎯 Next suggested actions:
  - Review and refine section content
  - Run `/rfpkit.compliance` to verify requirement coverage
  - Create additional sections as needed
  - Run `/rfpkit.pricing` if this is a cost/pricing section

## Content Quality Standards

### Evidence Requirements

Every claim must be supported by:
- **Specific metrics** (numbers, percentages, timeframes)
- **Case studies** with concrete results
- **Proof points** (certifications, past performance, capabilities)
- **Competitive differentiation** (what makes this unique vs competitors)

### Writing Style

- **Scannable structure**: Headers, bullet lists, tables
- **Front-loaded key points**: Most important information first
- **Active voice**: "We deliver" not "Deliverables will be provided"
- **Specific over generic**: "99.99% availability" not "high availability"
- **Customer-focused**: Emphasize customer benefits, not just features

### Win Theme Integration

Weave win themes throughout the section:
- Reference themes in key messages
- Support themes with evidence
- Connect themes to evaluation criteria
- Make themes memorable and repeatable

## Common Section Types

### Technical Approach Sections
Focus on: methodology, architecture, technologies, technical requirements, innovation, feasibility

### Management/Staffing Sections
Focus on: team structure, key personnel, qualifications, management approach, RACI, communication plan

### Past Performance Sections
Focus on: relevant case studies, similar projects, client references, lessons learned, quantified results

### Deliverables Sections
Focus on: deliverable descriptions, schedules, acceptance criteria, quality assurance, dependencies

### Pricing/Cost Sections
Focus on: pricing strategy, cost breakdown, value proposition, basis of estimate, assumptions

## Important Notes

- **No branch creation**: RFP Kit works directly with section files in `/sections/`
- **Template-driven**: Always follow the enhanced section-template.md structure
- **Evidence-based**: Include specific proof points, not generic claims
- **Compliance-focused**: Map all RFP requirements explicitly
- **Evaluation-optimized**: Structure content to maximize scoring potential

---

**Ready to create RFP section drafts!** Provide the section name/description and any specific requirements to address.
