# Tasks: Plugin Config Refactor

## Implementation Tasks

- [x] Move openclaw config from config/config.yaml to plugins/collectors/openclaw/plugin.yaml
- [x] Add config block to plugins/curators/openclaw/plugin.yaml
- [x] Update config/config.yaml: remove collector.openclaw, add plugins.active_collector/active_curator
- [x] Update backend/config/settings.py: add ACTIVE_COLLECTOR, ACTIVE_CURATOR, get_plugin_config()
- [x] Refactor backend/api/v1/collector.py: generic _load_collector_plugin(), /scan/active, /import/active
- [x] Refactor backend/api/v1/curator.py: generic _load_curator_plugin(), /evaluate/active/{id}
- [x] Write OpenSpec artifacts (proposal, specs, design, tasks)
