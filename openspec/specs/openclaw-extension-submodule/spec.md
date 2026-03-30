# openclaw-extension-submodule Specification

## Purpose
TBD - created by archiving change refactor-openclaw-collector. Update Purpose after archive.
## Requirements
### Requirement: OpenClaw Extension SHALL be a submodule
The system SHALL manage the OpenClaw Extension code (`openclaw-extension/`) outside of the core HarvestFlow repository directory structure, treating it as a Submodule or a completely decoupled repository for agent installations.

#### Scenario: Extension folder decoupling
- GIVEN the current codebase has a heavy nested `openclaw-extension/` directory
- WHEN the refactoring scripts run
- THEN the `openclaw-extension/` directory SHALL be isolated/moved or configured as a git submodule to `mcocdaa/harvestflow-openclaw-extension`.

