# openclaw-extension Specification

## Purpose
TBD - created by archiving change openclaw-extension. Update Purpose after archive.
## Requirements
### Requirement: OpenClaw Extension SHALL expose tools for HarvestFlow API interaction
The system SHALL provide an OpenClaw Extension that exposes standardized tools for AI Agents to interact with the HarvestFlow backend API.

#### Scenario: Tool Discovery
- GIVEN the OpenClaw Extension is installed and configured
- WHEN an Agent queries available tools
- THEN the Extension SHALL expose the following tools:
  - `harvestflow_list`
  - `harvestflow_scan_import`
  - `harvestflow_evaluate`
  - `harvestflow_review`

### Requirement: harvestflow_list tool SHALL query sessions and statistics
The system SHALL provide a `harvestflow_list` tool that allows Agents to query session data and system statistics.

#### Scenario: List Sessions
- GIVEN the HarvestFlow backend is accessible
- WHEN the Agent invokes `harvestflow_list` with optional filters (status, page, page_size)
- THEN the tool SHALL return a paginated list of sessions

#### Scenario: Get Session Details
- GIVEN a valid session_id exists
- WHEN the Agent invokes `harvestflow_list` with session_id parameter
- THEN the tool SHALL return detailed information about that session

#### Scenario: Get Statistics
- WHEN the Agent invokes `harvestflow_list` with stats=true
- THEN the tool SHALL return system-wide statistics including:
  - total_sessions
  - raw_sessions
  - approved_sessions
  - rejected_sessions
  - avg_auto_score
  - curated_sessions

### Requirement: harvestflow_scan_import tool SHALL scan and import sessions
The system SHALL provide a `harvestflow_scan_import` tool that allows Agents to scan folders for session files and import them into HarvestFlow.

#### Scenario: Scan Folder
- GIVEN a valid folder path
- WHEN the Agent invokes `harvestflow_scan_import` with action="scan"
- THEN the tool SHALL return a list of files found in the folder

#### Scenario: Import Single Session
- GIVEN a valid file path to a session file
- WHEN the Agent invokes `harvestflow_scan_import` with action="import" and file_path
- THEN the tool SHALL import the session and return the session_id

#### Scenario: Import All Sessions
- GIVEN a valid folder path containing session files
- WHEN the Agent invokes `harvestflow_scan_import` with action="import_all"
- THEN the tool SHALL import all valid sessions and return a summary of results

### Requirement: harvestflow_evaluate tool SHALL perform automated quality evaluation
The system SHALL provide a `harvestflow_evaluate` tool that allows Agents to trigger the Curator's automated quality evaluation on sessions.

#### Scenario: Evaluate Single Session
- GIVEN a valid session_id
- WHEN the Agent invokes `harvestflow_evaluate` with session_id
- THEN the tool SHALL trigger evaluation and return:
  - quality_auto_score
  - evaluation_status
  - evaluation_details

#### Scenario: Evaluate All Pending Sessions
- GIVEN there are sessions awaiting evaluation
- WHEN the Agent invokes `harvestflow_evaluate` without session_id (or with scope="all")
- THEN the tool SHALL trigger evaluation on all pending sessions and return a summary

#### Scenario: Get Curator Status
- WHEN the Agent invokes `harvestflow_evaluate` with action="status"
- THEN the tool SHALL return the current Curator configuration:
  - enabled status
  - auto_approve_threshold

### Requirement: harvestflow_review tool SHALL manage session review workflow
The system SHALL provide a `harvestflow_review` tool that allows Agents to perform review actions on sessions.

#### Scenario: Get Pending Reviews
- GIVEN there are sessions awaiting review
- WHEN the Agent invokes `harvestflow_review` with action="pending"
- THEN the tool SHALL return a list of sessions pending review

#### Scenario: Approve Session
- GIVEN a valid session_id
- WHEN the Agent invokes `harvestflow_review` with action="approve" and optional notes/score
- THEN the tool SHALL mark the session as approved and return the updated session

#### Scenario: Reject Session
- GIVEN a valid session_id
- WHEN the Agent invokes `harvestflow_review` with action="reject" and optional notes/score
- THEN the tool SHALL mark the session as rejected and return the updated session

#### Scenario: Batch Review
- GIVEN a list of session_ids
- WHEN the Agent invokes `harvestflow_review` with action="batch_approve" or "batch_reject"
- THEN the tool SHALL process all sessions and return a summary of results

### Requirement: Extension SHALL handle connection and authentication
The system SHALL provide robust connection handling and authentication mechanisms.

#### Scenario: Connection Configuration
- GIVEN the Extension is initialized
- WHEN configuration is provided via environment variables or config file
- THEN the Extension SHALL connect to the configured HarvestFlow backend URL

#### Scenario: Health Check
- WHEN the Extension starts or periodically
- THEN it SHALL verify connectivity to the HarvestFlow backend /health endpoint

#### Scenario: Error Handling
- GIVEN the HarvestFlow backend is unreachable
- WHEN any tool is invoked
- THEN the tool SHALL return a descriptive error message

