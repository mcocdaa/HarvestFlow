# Delta for Active Plugin Selection

## ADDED Requirements

### Requirement: Active Plugin Selection
The system SHALL allow selecting which collector and curator plugin is active via config.yaml.

#### Scenario: Switch active collector
- GIVEN `plugins.active_collector: openclaw` in config/config.yaml
- WHEN `POST /collector/scan/active` is called
- THEN the OpenClaw collector plugin is used and response includes `"plugin": "openclaw"`

#### Scenario: Switch to default collector
- GIVEN `plugins.active_collector: default` in config/config.yaml
- WHEN `POST /collector/scan/active` is called
- THEN the default file collector plugin is used

#### Scenario: Active curator evaluation
- GIVEN `plugins.active_curator: openclaw` in config/config.yaml
- WHEN `POST /curator/evaluate/active/{session_id}` is called
- THEN the OpenClaw curator plugin scores the session and response includes `"plugin": "openclaw"`
