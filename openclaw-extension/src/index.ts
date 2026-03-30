import { HarvestFlowClient } from './client';
import { harvestflowList } from './tools/list';
import { harvestflowScanImport } from './tools/scanImport';
import { harvestflowEvaluate } from './tools/evaluate';
import { harvestflowReview } from './tools/review';

export default function activate(context: any) {
  const config = context.config || {};
  const baseUrl = process.env.HARVESTFLOW_API_URL || config.HARVESTFLOW_API_URL || 'http://localhost:3001';
  const apiKey = process.env.HARVESTFLOW_API_KEY || config.HARVESTFLOW_API_KEY || '';

  const client = new HarvestFlowClient({ baseUrl, apiKey });

  context.registerTool('harvestflow_list', async (args: any) => {
    const result = await harvestflowList(client, args);
    return JSON.stringify(result, null, 2);
  });

  context.registerTool('harvestflow_scan_import', async (args: any) => {
    const result = await harvestflowScanImport(client, args);
    return JSON.stringify(result, null, 2);
  });

  context.registerTool('harvestflow_evaluate', async (args: any) => {
    const result = await harvestflowEvaluate(client, args);
    return JSON.stringify(result, null, 2);
  });

  context.registerTool('harvestflow_review', async (args: any) => {
    const result = await harvestflowReview(client, args);
    return JSON.stringify(result, null, 2);
  });

  console.log(`[HarvestFlow] Plugin activated. Target API: ${baseUrl}`);
}

export function deactivate() {
  console.log(`[HarvestFlow] Plugin deactivated.`);
}
