export type PluginType = 'collectors' | 'curators' | 'reviewers';

export interface Plugin {
  name: string;
  version: string;
  description: string;
  author: string;
  plugin_type: PluginType;
  frontend_entry?: string;
  enabled?: boolean;
}
