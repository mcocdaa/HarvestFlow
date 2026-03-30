## ADDED Requirements
None

## MODIFIED Requirements
### Requirement: OpenClaw Curator Plugin SHALL support AI tool score verification
The python `plugins/curators/openclaw/backend.py` file SHALL be restored to its original, uncorrupted UTF-8 baseline to remove Windows PowerShell-injected encoding garbles.

#### Scenario: Codebase restoration
- GIVEN the `openclaw` branch has corrupted python code from the previous commit
- WHEN the `git checkout origin/main` command runs against `plugins/curators/openclaw/backend.py`
- THEN the file SHALL contain its original non-garbled code and encoding.

## REMOVED Requirements
None
