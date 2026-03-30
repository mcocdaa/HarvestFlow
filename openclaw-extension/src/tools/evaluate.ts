import { HarvestFlowClient } from '../client';
import { ToolResult } from '../types';

export async function harvestflowEvaluate(
  client: HarvestFlowClient,
  args: any
): Promise<ToolResult<any>> {
  try {
    const scope = args.scope || 'single';
    const action = args.action || 'evaluate';

    if (action === 'status') {
      const status = await client.getCuratorStatus();
      return { success: true, data: status };
    }

    if (scope === 'all') {
      const result = await client.evaluateAll();
      return { success: true, data: result };
    }

    if (!args.session_id) {
      return { success: false, error: 'Missing required parameter: session_id' };
    }

    const result = await client.evaluateSession(args.session_id);
    return { success: true, data: result };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}
