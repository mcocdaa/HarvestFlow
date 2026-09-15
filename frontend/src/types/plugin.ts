export type PluginType = 'collectors' | 'curators' | 'reviewers' | 'services';

export interface Plugin {
  key: string;
  name: string;
  version: string;
  description: string;
  author: string;
  plugin_type: PluginType;
  type?: string;
  enabled: boolean;
}
