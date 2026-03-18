# Proposal: Plugin Config Refactor

## Summary
Move plugin-specific configuration out of the global `config/config.yaml` into each plugin's own `plugin.yaml`. Add an `active_collector` / `active_curator` selection mechanism so users can switch between `default` and `openclaw` plugins via config.

## Problem
The previous design put OpenClaw-specific settings (agents_dir, target_agents, etc.) inside `config/config.yaml` under `collector.openclaw`. This violates plugin encapsulation — the global config should not know about plugin internals.

## Proposed Solution

### 1. Plugin self-contained config
Each plugin's `plugin.yaml` gains a `config:` block with its own defaults:
```yaml
# plugins/collectors/openclaw/plugin.yaml
config:
  agents_dir: "C:/Users/20211/.openclaw/agents"
  target_agents: [backend_dev, req_analyst, qa_ops, coord]
  skip_cron_sessions: true
  min_message_count: 5
```

### 2. Active plugin selection in global config
```yaml
# config/config.yaml
plugins:
  dir: ./plugins
  active_collector: openclaw   # or: default
  active_curator: openclaw     # or: default
```

### 3. Helper function
`backend/config/settings.py` exposes `get_plugin_config(plugin_type, plugin_name)` to read a plugin's config block from its plugin.yaml.

### 4. Unified API endpoints
- `POST /collector/scan/active` — uses active_collector plugin
- `POST /collector/import/active` — uses active_collector plugin
- `POST /curator/evaluate/active/{id}` — uses active_curator plugin
- Old `/scan/openclaw` and `/import/openclaw` kept as deprecated aliases

## Rollback Plan
Change `active_collector: default` and `active_curator: default` in config.yaml to revert to original behavior.
