# Delta for OpenClaw Integration

## ADDED Requirements

### Requirement: OpenClaw Collector Plugin
The system SHALL provide a collector plugin that reads OpenClaw Agent session data from the local filesystem.

#### Scenario: Scan sessions
- GIVEN the `agents_dir` is configured and exists
- WHEN `/collector/scan/openclaw` is called
- THEN the system returns a list of .jsonl file paths for all non-cron sessions of target agents

#### Scenario: Parse session file
- GIVEN a valid .jsonl session file path
- WHEN the collector parses the file
- THEN it returns a structured dict with: session_id, agent_id, messages, tools_used, has_tool_calls, message_count
- AND sessions with fewer messages than `min_message_count` are filtered out

#### Scenario: Skip cron sessions
- GIVEN a sessions.json index containing cron session keys (containing `:cron:`)
- WHEN `skip_cron_sessions` is true
- THEN those sessions are excluded from scan results

### Requirement: OpenClaw Curator Plugin
The system SHALL provide a curator plugin that scores OpenClaw sessions using Agent-specific quality criteria.

#### Scenario: Score by tool call success
- GIVEN a session with `has_tool_calls=True` and no error in tool_result
- WHEN the curator evaluates the session
- THEN the score increases by 1 and reason "工具调用成功" is recorded

#### Scenario: Score by decision chain
- GIVEN a session with ≥3 assistant messages each containing tool_use
- WHEN the curator evaluates the session
- THEN the score increases by 1 and reason "多步决策链" is recorded

#### Scenario: Score by explicit output
- GIVEN a session where an assistant message contains ≥2 occurrences of ``` or a file path with known extension
- WHEN the curator evaluates the session
- THEN the score increases by 1 and reason "明确的最终输出" is recorded

#### Scenario: High value threshold
- GIVEN a session with score ≥ 3
- WHEN evaluation completes
- THEN `is_high_value` is set to True

### Requirement: OpenClaw API Endpoints
The system SHALL expose two new REST endpoints for OpenClaw integration.

#### Scenario: Scan endpoint
- GIVEN the backend is running
- WHEN `POST /api/v1/collector/scan/openclaw` is called
- THEN it returns `{total, files}` listing discovered session files

#### Scenario: Import endpoint
- GIVEN the backend is running
- WHEN `POST /api/v1/collector/import/openclaw` is called
- THEN it scans, parses, and imports all valid sessions into the database
- AND returns `{total, imported, failed, session_ids, failed_files}`

### Requirement: OpenClaw Config Block
The system SHALL support openclaw-specific configuration in `config/config.yaml`.

#### Scenario: Config loading
- GIVEN `collector.openclaw` block exists in config.yaml
- WHEN the collector plugin is instantiated
- THEN it reads agents_dir, target_agents, skip_cron_sessions, min_message_count from config
