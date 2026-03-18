# Delta for API Endpoints

## ADDED Requirements

### Requirement: OpenClaw Scan Endpoint
The system SHALL expose a REST endpoint to scan OpenClaw sessions.

#### Scenario: Scan returns file list
- GIVEN the backend is running and openclaw config is present
- WHEN `POST /api/v1/collector/scan/openclaw` is called
- THEN it returns `{"total": N, "files": [...]}`

### Requirement: OpenClaw Import Endpoint
The system SHALL expose a REST endpoint to import OpenClaw sessions into the database.

#### Scenario: Import all valid sessions
- GIVEN the backend is running
- WHEN `POST /api/v1/collector/import/openclaw` is called
- THEN it scans, parses, and imports all sessions meeting the min_message_count threshold
- AND returns `{"total": N, "imported": M, "failed": K, "session_ids": [...], "failed_files": [...]}`
