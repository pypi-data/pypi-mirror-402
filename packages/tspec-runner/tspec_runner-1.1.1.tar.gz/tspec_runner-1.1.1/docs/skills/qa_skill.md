# AgentSkills - QA & Testing
Records AgentSkills that focus on quality assurance (pytest, tspec doctor, release validation) per https://agentskills.io/home.

## Purpose
- Surface QA-related agents for test/spec coverage, release checklists, and documentation validation.
- Enable fast discovery of QA skill instructions when spec/test reports are mentioned.
- Reference `skills/webapp-testing` for automated test flows and `skills/internal-comms` for reporting results to stakeholders, matching the Anthropic pattern of pairing test execution with communication guidance.

## Workflow
1. Before acting on QA/test tasks (pytest, `tspec doctor`, release notes), load this file to align with the right AgentSkill.
2. Track test coverage, environment setup notes, and any blocking issues under the “Checklist” section.
3. Update “Key resources” whenever a new QA tool or report is introduced from the catalog.

## Checklist
- Ensure pytest and `tspec doctor` results are recorded when rerun.
- For release uploads, double-check documentation in `docs/Knowledge.md`.
- Reminder: `tspec doctor --unreal-mcp-health` expects the Unreal MCP helper to already be connected to a running engine; a `WinError 10061` usually means the project/play mode isn’t started yet, not a missing package.

## Notes
- Last synced: TODO.
