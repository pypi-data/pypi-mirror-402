# RFP Kit

**A framework for structured RFP response development using AI agents.**

RFP Kit helps teams create high-quality, consistent RFP responses by applying structured workflows with AI assistance. It's based on the proven Spec-Driven Development methodology, adapted for the RFP response process.

## Quick Start

### Installation

```bash
pip install -e .
```

### Initialize Your First RFP Response

```bash
rfpkit init acme-cloud-platform-rfp --ai copilot --script sh
cd acme-cloud-platform-rfp
```

### The RFP Response Workflow

1. **Establish Guidelines** - Define your RFP response principles
   ```
   /rfpkit.guidelines
   ```

2. **Define Section** - Specify RFP section requirements
   ```
   /rfpkit.section Technical Architecture (Section 3.2)
   ```

3. **Create Strategy** - Plan your response approach
   ```
   /rfpkit.strategy We're using AWS multi-region architecture
   ```

4. **Generate Tasks** - Break down the writing work
   ```
   /rfpkit.tasks
   ```

5. **Draft Response** - Let AI generate your content
   ```
   /rfpkit.draft
   ```

## What You Get

After running `rfpkit init`, your project will have:

```
your-rfp-project/
├── .github/agents/          # AI slash commands (for GitHub Copilot)
│   ├── guidelines.md        # /rfpkit.guidelines
│   ├── section.md           # /rfpkit.section
│   ├── strategy.md          # /rfpkit.strategy
│   ├── tasks.md             # /rfpkit.tasks
│   └── draft.md             # /rfpkit.draft
├── .specify/
│   ├── scripts/             # Automation scripts
│   └── templates/           # Document templates
├── memory/
│   └── constitution.md      # Your RFP response guidelines
└── specs/                   # RFP section responses (created by workflow)
    └── 1-technical-arch/
        ├── SPEC.md          # Requirements extracted from RFP
        ├── PLAN.md          # Response strategy
        ├── TASKS.md         # Writing checklist
        └── response.md      # Final drafted content
```

## Supported AI Agents

RFP Kit works with all major AI coding assistants:

- **GitHub Copilot** (`.github/agents/`)
- **Claude Code** (`.claude/commands/`)
- **Cursor** (`.cursor/commands/`)
- **Windsurf** (`.windsurf/workflows/`)
- And many more...

Choose your preferred AI agent during `rfpkit init`.

## Key Features

✅ **Structured Workflow** - Clear phases from requirements to draft  
✅ **AI-Powered Writing** - Let AI draft content following your guidelines  
✅ **Version Control** - Track all iterations with Git  
✅ **Reusable Patterns** - Templates evolve with your RFP experience  
✅ **Quality Checklists** - Ensure completeness and compliance  
✅ **Cross-Platform** - Works on macOS, Linux, and Windows

## Example Workflow

```bash
# 1. Initialize RFP project
rfpkit init aws-migration-rfp --ai copilot --script sh
cd aws-migration-rfp

# 2. Set response guidelines
/rfpkit.guidelines Create guidelines focused on security compliance

# 3. Define first section
/rfpkit.section Executive Summary (Page limit: 2 pages)

# 4. Plan the response
/rfpkit.strategy Emphasize our 15-year AWS partnership and SOC2 compliance

# 5. Generate tasks
/rfpkit.tasks

# 6. Draft content
/rfpkit.draft

# Result: specs/1-executive-summary/ contains your drafted response!
```

## Advanced Usage

### Multiple Sections

Each RFP section becomes its own "feature":

```
specs/
├── 1-executive-summary/
├── 2-technical-architecture/
├── 3-pricing-commercial/
└── 4-implementation-timeline/
```

### Optional Commands

- `/rfpkit.clarify` - Ask questions before planning
- `/rfpkit.analyze` - Check consistency across sections
- `/rfpkit.checklist` - Validate response quality

## Development Status

**Version**: 0.1.0 (Phase 1 - Minimal Fork)

This is an evolutionary fork of [Spec Kit](https://github.com/github/spec-kit), adapted for RFP response workflows.

### Roadmap

- **Phase 1** (Current): Core rebranding and basic RFP workflow
- **Phase 2** (Next): Enhanced RFP-specific templates and content
- **Phase 3** (Future): Advanced commands (competitive analysis, compliance matrix)
- **Phase 4** (Future): Polish, testing, and team scaling

## Origin

RFP Kit is based on [GitHub Spec Kit](https://github.com/github/spec-kit) - a framework for Spec-Driven Development. We've adapted the proven workflow patterns for RFP response management.

## License

Same as original Spec Kit (check LICENSE file in repository).

## Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Share tips and ask questions in Discussions
- **Original Spec Kit Docs**: [spec-kit documentation](https://github.com/github/spec-kit)

---

**Ready to transform your RFP process?** Install RFP Kit and start your first structured response today!
