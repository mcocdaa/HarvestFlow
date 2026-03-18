# Design: Plugin Config Refactor

## Changes

### config/config.yaml
- Removed: `collector.openclaw` block
- Added: `plugins.active_collector` and `plugins.active_curator` fields

### plugins/collectors/openclaw/plugin.yaml
- Added: `config:` block with agents_dir, target_agents, skip_cron_sessions, min_message_count

### plugins/curators/openclaw/plugin.yaml
- Added: `config:` block with auto_approve_threshold, high_value_min_score

### backend/config/settings.py
- Added: `ACTIVE_COLLECTOR`, `ACTIVE_CURATOR` constants (read from config.yaml)
- Added: `get_plugin_config(plugin_type, plugin_name)` helper

### backend/api/v1/collector.py
- Refactored: `_load_collector_plugin(plugin_name)` — generic loader for any collector
- Added: `POST /collector/scan/active` and `POST /collector/import/active`
- Kept: `/scan/openclaw` and `/import/openclaw` as deprecated aliases

### backend/api/v1/curator.py
- Added: `_load_curator_plugin(plugin_name)` — generic loader for any curator
- Added: `POST /curator/evaluate/active/{session_id}`
- Updated: `GET /curator/config` now returns active_curator and plugin_config
