# Design: OpenClaw Integration

## Architecture

### Plugin Loading
Both plugins use the existing `PluginLoader` infrastructure. The API endpoints use `importlib.util` for dynamic loading to avoid Python path issues (backend runs from `backend/` directory, plugins live in `plugins/` at project root).

### Data Flow
```
OpenClaw agents dir
  └── {agent_id}/sessions/sessions.json   ← index (session_key → metadata + sessionFile path)
  └── {agent_id}/sessions/{session_id}.jsonl  ← actual conversation (JSONL, one message per line)
        ↓
  OpenClawCollector.scan()   → list of .jsonl paths
  OpenClawCollector.parse()  → structured session dict
        ↓
  OpenClawCurator.evaluate() → {score, is_high_value, tags, score_reasons}
        ↓
  session_manager.create_session() → stored in SQLite sessions table
```

### Message Format (OpenClaw JSONL)
Each line in a .jsonl file is a JSON object:
```json
{
  "role": "user" | "assistant",
  "content": "string" | [{"type": "text", "text": "..."}, {"type": "tool_use", "name": "exec", "input": {...}}, {"type": "tool_result", "content": "..."}]
}
```

### Scoring Algorithm
| Condition | Points |
|-----------|--------|
| Base | 2 |
| Tool call success | +1 |
| Decision chain (≥3 tool turns) | +1 |
| Explicit output (code block or file path) | +1 |
| message_count > 20 | +1 |
| **Max** | **5** |

High value threshold: score ≥ 3

### Key Design Decisions
1. **Dynamic plugin loading** via `importlib.util` in collector.py — avoids import path issues between `backend/` and `plugins/`
2. **sessionFile is absolute path** — OpenClaw stores full Windows paths in sessions.json, no path joining needed
3. **Cron session filtering** — session keys containing `:cron:` are skipped by default
4. **Content normalization** — `_parse_content()` handles both string and array content formats, extracting text while annotating tool calls
