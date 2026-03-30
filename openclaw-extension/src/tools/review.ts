import { HarvestFlowClient } from '../client';
import { ToolResult } from '../types';

export async function harvestflowReview(
  client: HarvestFlowClient,
  args: any
): Promise<ToolResult<any>> {
  try {
    const action = args.action;

    if (!action) {
      return { success: false, error: 'Missing required parameter: action' };
    }

    if (action === 'pending') {
      const page = args.page ? parseInt(args.page, 10) : 1;
      const pageSize = args.page_size ? parseInt(args.page_size, 10) : 20;
      const pending = await client.getPendingReviews(page, pageSize);
      return { success: true, data: pending };
    }

    if (action === 'approve') {
      if (!args.session_id) {
        return { success: false, error: 'Missing required parameter: session_id' };
      }
      const score = args.score ? parseFloat(args.score) : undefined;
      const result = await client.approveSession(args.session_id, args.notes, score);
      return { success: true, data: result };
    }

    if (action === 'reject') {
      if (!args.session_id) {
        return { success: false, error: 'Missing required parameter: session_id' };
      }
      const score = args.score ? parseFloat(args.score) : undefined;
      const result = await client.rejectSession(args.session_id, args.notes, score);
      return { success: true, data: result };
    }

    if (action === 'batch_approve') {
      if (!args.session_ids || !Array.isArray(args.session_ids)) {
        return { success: false, error: 'Missing or invalid parameter: session_ids (must be array)' };
      }
      const result = await client.batchApprove(args.session_ids);
      return { success: true, data: result };
    }

    if (action === 'batch_reject') {
      if (!args.session_ids || !Array.isArray(args.session_ids)) {
        return { success: false, error: 'Missing or invalid parameter: session_ids (must be array)' };
      }
      const result = await client.batchReject(args.session_ids);
      return { success: true, data: result };
    }

    return { success: false, error: `Invalid action: ${action}` };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}
