# extension-submodule-migration Specification

## Purpose
TBD - created by archiving change move-extension-to-submodule. Update Purpose after archive.
## Requirements
### Requirement: OpenClaw Extension SHALL be included as a Git Submodule
The system SHALL remove the root `openclaw-extension/` directory and replace it with a `git submodule` linkage pointing to `git@github.com:mcocdaa/plugin-openclaw-to-harvestflow.git`.

#### Scenario: Verify submodule addition
- GIVEN the current repository branch `openclaw`
- WHEN the user initializes and runs the update scripts
- THEN the system SHALL place the Submodule inside `plugins/plugin-openclaw-to-harvestflow` and NOT track the TypeScript source files directly in HarvestFlow root.

