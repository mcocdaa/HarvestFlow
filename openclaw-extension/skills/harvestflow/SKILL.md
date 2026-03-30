# HarvestFlow OpenClaw Skill

## Overview

This skill provides integration with HarvestFlow - AI Agent session data collection and curation platform. Use it to import, evaluate, and review AI agent conversation sessions for dataset creation.

## Tools

### 1. harvestflow_list

List sessions or get session statistics.

**Parameters:**
- `session_id` (optional): Get details for a specific session
- `status` (optional): Filter by status (`raw` | `approved` | `rejected`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `stats` (optional): Return overall statistics (boolean)

**Examples:**
```json
// Get statistics
{"stats": true}

// List approved sessions
{"status": "approved", "page": 1, "page_size": 10}

// Get a specific session
{"session_id": "abc-123"}
```

### 2. harvestflow_scan_import

Scan folders and import session files into HarvestFlow.

**Parameters:**
- `action` (required): `scan` | `import` | `import_all`
  - `scan`: Scan a folder for session files without importing
  - `import`: Import a single session file
  - `import_all`: Import all session files from a folder
- `folder_path` (optional): Folder path to scan/import (uses default configured folder if not provided)
- `file_path` (required for `import`): Path to single session file

**Examples:**
```json
// Scan a folder
{"action": "scan", "folder_path": "C:/sessions"}

// Import a single file
{"action": "import", "file_path": "C:/sessions/session-1.jsonl"}

// Import all from folder
{"action": "import_all", "folder_path": "C:/sessions"}
```

### 3. harvestflow_evaluate

Run AI evaluation on imported sessions.

**Parameters:**
- `session_id` (required for `single`): Session ID to evaluate
- `scope` (optional): `single` (default) | `all`
- `action` (optional): `evaluate` (default) | `status`

**Examples:**
```json
// Evaluate a single session
{"session_id": "abc-123", "scope": "single"}

// Evaluate all pending sessions
{"scope": "all"}

// Get current curator status
{"action": "status"}
```

### 4. harvestflow_review

Human review of evaluated sessions (approve/reject).

**Parameters:**
- `action` (required): `pending` | `approve` | `reject` | `batch_approve` | `batch_reject`
  - `pending`: List sessions pending review
  - `approve`: Approve a session (add to dataset)
  - `reject`: Reject a session
  - `batch_approve`: Approve multiple sessions
  - `batch_reject`: Reject multiple sessions
- `session_id` (required for `approve`/`reject`): Single session ID
- `session_ids` (required for batch operations): Array of session IDs
- `notes` (optional): Review notes
- `score` (optional): Manual quality score (0-100)
- `page` (optional): Page number for pending list (default: 1)
- `page_size` (optional): Page size for pending list (default: 20)

**Examples:**
```json
// List pending sessions
{"action": "pending"}

// Approve a session
{"action": "approve", "session_id": "abc-123", "notes": "Good quality conversation", "score": 90}

// Reject a session
{"action": "reject", "session_id": "def-456", "notes": "Off-topic conversation"}

// Batch approve
{"action": "batch_approve", "session_ids": ["abc-123", "ghi-789"]}
```

## Configuration

Configure these settings in your OpenClaw config or environment variables:

| Environment Variable       | Config Key               | Default               | Description                              |
|----------------------------|--------------------------|-----------------------|------------------------------------------|
| `HARVESTFLOW_API_URL`      | `HARVESTFLOW_API_URL`    | `http://localhost:3001` | HarvestFlow backend API URL             |
| `HARVESTFLOW_API_KEY`      | `HARVESTFLOW_API_KEY`    | (empty)               | Optional API key for authentication      |

## Workflow

Typical workflow when curating a dataset:

1. **Scan**: `harvestflow_scan_import` with `action=scan` to find session files
2. **Import**: `harvestflow_scan_import` with `action=import_all` to import all discovered sessions
3. **List**: `harvestflow_list` with `stats=true` to check import progress
4. **Evaluate**: `harvestflow_evaluate` with `scope=all` to run AI evaluation on all sessions
5. **Review**:
   - `harvestflow_review` with `action=pending` to get list of evaluated sessions
   - Approve or reject each session
   - Use batch operations for faster review
6. **Final check**: `harvestflow_list` with `stats=true` to get final dataset statistics

## Troubleshooting

### Connection Error
- Verify HarvestFlow backend is running
- Check `HARVESTFLOW_API_URL` configuration
- Ensure the port is open and accessible

### Session Not Found
- Verify the session ID is correct using `harvestflow_list`
- Check that the session was successfully imported

### Import Errors
- Verify file paths are correct and accessible
- Check file format: HarvestFlow expects JSONL or JSON session files

## See Also

- HarvestFlow documentation: https://github.com/your-org/harvestflow
- OpenClaw Extension documentation: https://github.com/openclaw/extensions