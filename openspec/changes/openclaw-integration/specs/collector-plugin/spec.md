# Delta for Collector Plugin

## ADDED Requirements

### Requirement: OpenClaw Session Scanning
The system SHALL scan OpenClaw Agent session files from the local filesystem.

#### Scenario: Scan target agents
- GIVEN `agents_dir` is configured and target_agents list is non-empty
- WHEN `POST /api/v1/collector/scan/openclaw` is called
- THEN the system reads sessions.json for each target agent and returns a list of .jsonl file paths

#### Scenario: Skip cron sessions
- GIVEN a sessions.json containing session keys with `:cron:` substring
- WHEN `skip_cron_sessions` is true (default)
- THEN those session files are excluded from results

#### Scenario: Filter by message count
- GIVEN a parsed session with fewer messages than `min_message_count`
- WHEN the collector parses the file
- THEN the session is discarded and not returned

### Requirement: OpenClaw Session Parsing
The system SHALL parse OpenClaw .jsonl files into a structured session format.

#### Scenario: Parse JSONL messages
- GIVEN a valid .jsonl file with one JSON object per line
- WHEN the collector parses it
- THEN it returns a dict with session_id, agent_id, messages, tools_used, has_tool_calls, message_count

#### Scenario: Handle array content
- GIVEN an assistant message where content is an array of typed blocks
- WHEN the collector parses the message
- THEN text blocks are concatenated, tool_use blocks are annotated as `[tool_use: name]`, tool_result as `[tool_result]`
