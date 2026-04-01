## ADDED Requirements

### Requirement: OpenClaw Curator Plugin SHALL support AI tool score verification
The python `plugins/curators/openclaw/backend.py` file SHALL be refactored to correctly identify AI tool execution signatures (`tool_use` and `tool_result` tags inside JSON payloads) properly cross-referenced by the actual JSON structure output by OpenClaw extensions.

#### Scenario: Robust tool parsing in python
- GIVEN the curator analyzes a session JSON structure
- WHEN the session has `has_tool_calls = True`
- THEN the script SHALL correctly navigate the nested `msg.get("content")` list without raising `AttributeError` or `KeyError` on unexpected keys.

## MODIFIED Requirements
None

## REMOVED Requirements
None
