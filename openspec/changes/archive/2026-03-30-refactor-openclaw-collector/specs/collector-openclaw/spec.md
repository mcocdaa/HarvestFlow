## ADDED Requirements

### Requirement: OpenClaw Collector Plugin SHALL handle API Ingestion gracefully
The python `plugins/collectors/openclaw/backend.py` file SHALL be refactored to remove hardcoded Windows paths (like `C:/Users/20211/.openclaw/agents`). It MUST resolve paths via OS-agnostic calls or configuration keys.

#### Scenario: Scan sessions using dynamic paths
- GIVEN the config specifies an OS-agnostic `agents_dir` or is empty
- WHEN `scan()` is invoked
- THEN the script SHALL use robust python Path joining tools (`os.path` / `pathlib`) and MUST NOT perform blind string replacement of `C:\\` drive paths.

#### Scenario: Allow missing agent paths
- GIVEN an agent ID in `target_agents` does not exist
- WHEN `scan()` runs
- THEN the script SHALL log a warning but MUST NOT raise exception or crash.

## MODIFIED Requirements
None

## REMOVED Requirements
None
