# HTML Review Artifact Skill

## Purpose

Create self-contained HTML artifacts that help humans review, understand, compare, and make decisions about complex technical work.

This skill is for:
- architecture reviews
- implementation plans
- PR explainers
- technical explainers
- decision briefs

This skill is not for:
- decorative landing pages
- marketing websites
- generic documentation
- long linear prose converted into HTML

## Core Principle

Optimize for human review and decision support.

A good artifact should make the reader understand:
- what the subject is
- why it matters
- how the system or idea is structured
- what the important decisions are
- what risks or uncertainties exist
- what should happen next

## Output Requirements

Generate a single self-contained `.html` file unless the user asks otherwise.

The file must:
- open directly in a browser
- include inline CSS
- include inline SVG where diagrams are needed
- avoid external CDN dependencies
- avoid requiring a build step
- be readable on desktop and reasonably readable on mobile

## Visual and Structural Rules

Prefer:
- SVG diagrams over ASCII diagrams
- cards for grouped concepts
- tables for comparisons
- callouts for risks, decisions, and assumptions
- side-by-side layouts for tradeoffs
- collapsible sections for detailed evidence
- sticky or clear navigation for long artifacts

Avoid:
- ASCII diagrams
- excessive animation
- decorative visual noise
- marketing-site aesthetics
- long unbroken prose
- framework complexity unless explicitly requested

## Supported Artifact Types

### architecture-review

Use when reviewing a system, repository, module, platform, or technical architecture.

Include:
- executive summary
- system context
- architecture diagram
- major components and responsibilities
- data/control flow
- key design decisions
- risks and gaps
- recommended next steps

### implementation-plan

Use when planning implementation work.

Include:
- goal
- scope
- assumptions
- task breakdown
- dependency map
- implementation sequence
- risks
- verification plan

### pr-explainer

Use when explaining or reviewing a pull request.

Include:
- summary of change
- files/modules changed
- behavior before/after
- important diffs or code snippets
- risk assessment
- review checklist
- suggested follow-up work

### technical-explainer

Use when explaining a technical concept or subsystem.

Include:
- concept overview
- mental model
- diagram
- key mechanisms
- examples
- common pitfalls
- references to relevant files if available

### decision-brief

Use when comparing options or supporting a decision.

Include:
- decision to be made
- options
- comparison table
- tradeoffs
- recommendation
- risks
- next actions

## Evidence and Traceability

When source files, code, issues, PRs, or documents are available:
- reference the relevant files or modules
- distinguish facts from assumptions
- show how conclusions were derived
- identify missing information explicitly

## Interaction Rules

Interactive elements are allowed only when they improve review or decision-making.

Useful interactions include:
- tabs
- filters
- collapsible sections
- layer toggles
- copy buttons
- simple parameter controls

Avoid interaction for its own sake.

## Final Check

Before finishing, verify that the artifact:
- can be opened as a standalone HTML file
- has a clear title and purpose
- has an executive summary or equivalent overview
- includes at least one visual structure when useful
- highlights risks, decisions, and next steps
- is easier to review than an equivalent Markdown document
