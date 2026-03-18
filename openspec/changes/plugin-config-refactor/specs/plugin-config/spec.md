# Delta for Plugin Config

## ADDED Requirements

### Requirement: Plugin Self-Contained Configuration
The system SHALL store plugin-specific configuration inside the plugin's own plugin.yaml under a `config:` block. The global config/config.yaml SHALL NOT contain plugin-specific settings.

#### Scenario: Read plugin config from plugin.yaml
- GIVEN a plugin.yaml with a `config:` block containing plugin-specific settings
- WHEN `get_plugin_config("collectors", "openclaw")` is called
- THEN it returns the config dict from that plugin's plugin.yaml

#### Scenario: Plugin instantiation with own config
- GIVEN active_collector is set to "openclaw"
- WHEN the collector endpoint is called
- THEN the OpenClawCollector MUST be instantiated with config read from plugins/collectors/openclaw/plugin.yaml, not from config/config.yaml

## REMOVED Requirements

### Requirement: Global Config Plugin Settings
(Reason: Plugin settings belong in plugin.yaml, not in the global config. Removing collector.openclaw block from config/config.yaml.)
