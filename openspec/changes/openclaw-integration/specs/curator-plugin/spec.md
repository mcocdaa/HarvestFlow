# Delta for Curator Plugin

## ADDED Requirements

### Requirement: OpenClaw Session Scoring
The system SHALL score OpenClaw sessions using Agent-specific quality criteria.

#### Scenario: Score tool call success
- GIVEN a session with `has_tool_calls=True` and no error string in tool_result content
- WHEN the curator evaluates the session
- THEN score increases by 1 and "工具调用成功" is added to score_reasons

#### Scenario: Score decision chain
- GIVEN a session where ≥3 assistant messages each contain at least one tool_use block
- WHEN the curator evaluates the session
- THEN score increases by 1 and "多步决策链" is added to score_reasons

#### Scenario: Score explicit output
- GIVEN a session where an assistant message contains ≥2 occurrences of ``` or a file path with extension (.py/.ts/.json/.md etc.)
- WHEN the curator evaluates the session
- THEN score increases by 1 and "明确的最终输出" is added to score_reasons

#### Scenario: High value classification
- GIVEN a session with final score ≥ 3 (out of max 5)
- WHEN evaluation completes
- THEN `is_high_value` is set to True
