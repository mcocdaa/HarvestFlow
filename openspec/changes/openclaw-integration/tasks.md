# Tasks: OpenClaw Integration

## Implementation Tasks

- [x] Create `plugins/collectors/openclaw/plugin.yaml`
- [x] Create `plugins/collectors/openclaw/backend.py`
  - [x] `OpenClawCollector.__init__()` — load config (agents_dir, target_agents, skip_cron, min_message_count)
  - [x] `OpenClawCollector.scan()` — iterate target agents, read sessions.json, filter cron sessions, return .jsonl paths
  - [x] `OpenClawCollector.parse()` — read .jsonl line by line, extract messages/tools/metadata
  - [x] `OpenClawCollector._parse_content()` — normalize string/array content
  - [x] `OpenClawCollector._extract_metadata()` — look up session info from sessions.json
- [x] Create `plugins/curators/openclaw/plugin.yaml`
- [x] Create `plugins/curators/openclaw/backend.py`
  - [x] `OpenClawCurator.evaluate()` — run 3 criteria checks, compute score, extract tags
  - [x] `OpenClawCurator._check_tool_call_success()` — has_tool_calls + no error
  - [x] `OpenClawCurator._check_decision_chain()` — ≥3 assistant turns with tool_use
  - [x] `OpenClawCurator._check_explicit_output()` — code blocks or file paths
  - [x] `OpenClawCurator._extract_tags()` — agent_id, tools_used, keyword tags
- [x] Update `config/config.yaml` — add `collector.openclaw` block
- [x] Update `backend/api/v1/collector.py`
  - [x] Add `_load_openclaw_collector()` dynamic loader
  - [x] Add `POST /collector/scan/openclaw` endpoint
  - [x] Add `POST /collector/import/openclaw` endpoint
- [x] Initialize OpenSpec in project (`openspec init`)
- [x] Write proposal.md, specs.md, design.md, tasks.md
- [x] Commit and push to `feature/openclaw-integration`
- [x] Create PR #1 on GitHub

## Bug Fixes Applied
- [x] Fixed: `sessionFile` is absolute path — removed incorrect path joining in `scan()`
- [x] Fixed: metadata lookup uses full path comparison, not just basename
- [x] Fixed: collector.py uses dynamic import instead of direct module import to avoid path issues
