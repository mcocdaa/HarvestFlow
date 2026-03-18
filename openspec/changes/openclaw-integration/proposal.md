# Proposal: OpenClaw Integration

## Summary
Add OpenClaw-specific collector and curator plugins to HarvestFlow, enabling automatic extraction of high-quality LoRA training data from local OpenClaw Agent session files.

## Problem
HarvestFlow currently only supports scanning generic JSON files from watched folders. There is no native integration with OpenClaw's session storage format (sessions.json index + .jsonl conversation files), making it impossible to automatically harvest training data from Agent conversations.

## Proposed Solution
Implement two new plugins:
1. **OpenClaw Collector** (`plugins/collectors/openclaw/`) — reads OpenClaw session files directly from the local filesystem
2. **OpenClaw Curator** (`plugins/curators/openclaw/`) — scores sessions using domain-specific criteria tailored to Agent conversations

Plus two new API endpoints and config updates to wire everything together.

## Scope

### In Scope
- OpenClaw collector plugin (scan + parse sessions.json + .jsonl)
- OpenClaw curator plugin (3-criteria scoring: tool calls, decision chain, explicit output)
- Config block for openclaw collector settings
- Two new API endpoints: `/collector/scan/openclaw` and `/collector/import/openclaw`

### Out of Scope
- Frontend UI changes
- Automated scheduling / cron-based collection
- Support for remote/cloud OpenClaw deployments

## Target Agents
- `backend_dev` — code writing, debugging, implementation
- `req_analyst` — requirements analysis, task decomposition
- `qa_ops` — quality assurance, testing
- `coord` — coordination and orchestration

## High-Value Criteria (any 1 = high value)
| Criterion | Definition |
|-----------|-----------|
| Tool call success | Session has tool_use + no error in tool_result |
| Decision chain | ≥3 assistant turns each containing tool_use |
| Explicit output | Code blocks (```) or file paths in assistant messages |

## Rollback Plan
Plugins are isolated in `plugins/` directory. Disabling the openclaw plugins in config.yaml reverts to default behavior with zero impact on existing functionality.

## Implementation Status
**Already implemented** in branch `feature/openclaw-integration` (PR #1). This spec documents the change retroactively for traceability.
