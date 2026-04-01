## 1. Setup and OpenClaw Extension Submodule Preparation

- [x] 1.1 Create a temporary backup of `openclaw-extension/` outside the workspace (if needed).
- [x] 1.2 Remove the directory `openclaw-extension/` from HarvestFlow git tracking (or move it into a proper submodule git reference).
- [x] 1.3 Add a generic `README` entry or `git submodule add` command referencing `git@github.com:mcocdaa/harvestflow-openclaw-extension.git` (or the equivalent openclaw standalone repo). *Note: since the remote repo for the submodule might not exist yet, we will just delete the folder from main tracking and leave a note/script*.

## 2. Refactor Python Collector (`plugins/collectors/openclaw/backend.py`)

- [x] 2.1 Replace the hardcoded `DEFAULT_AGENTS_DIR = "C:/Users/20211/.openclaw/agents"` with an OS-agnostic path resolving to the user's home dir or reading from env.
- [x] 2.2 In `scan()`, replace the brittle Windows string logic (`session_file.split('\\')[-1]`) with `os.path.basename()` or `pathlib.Path().name`.
- [x] 2.3 Ensure error blocks log gracefully when agent directories are completely missing rather than spamming errors that fail tests.

## 3. Refactor Python Curator (`plugins/curators/openclaw/backend.py`)

- [x] 3.1 In `_check_decision_chain()`, add safety checks (`isinstance(content, str)`) before assuming content is a `list`.
- [x] 3.2 In `_check_explicit_output()`, gracefully handle empty or malformed strings so `count("```")` doesn't crash on None.

## 4. Finalize

- [x] 4.1 Commit all python refactoring changes to the `openclaw` branch.
- [x] 4.2 Push branch to remote.
- [x] 4.3 Create Pull Request (MR) against `main`.
