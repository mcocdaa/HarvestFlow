import axios, { AxiosInstance } from 'axios';
import {
  ListParams,
  SessionListResponse,
  Session,
  StatsResponse,
  ScanResponse,
  ImportResponse,
  ImportAllResponse,
  EvaluateResponse,
  EvaluateAllResponse,
  PendingResponse,
  ReviewResponse,
  BatchReviewResponse
} from './types';

export class HarvestFlowClient {
  private client: AxiosInstance;

  constructor(config: { baseUrl: string; apiKey?: string }) {
    this.client = axios.create({
      baseURL: config.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        ...(config.apiKey ? { 'Authorization': `Bearer ${config.apiKey}` } : {})
      }
    });

    // Error handling middleware
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        let message = 'HarvestFlow API Error';
        if (error.response) {
          message = `API Error [${error.response.status}]: ${JSON.stringify(error.response.data)}`;
        } else if (error.request) {
          message = 'Connection Error: Cannot reach HarvestFlow backend';
        } else {
          message = `Error: ${error.message}`;
        }
        return Promise.reject(new Error(message));
      }
    );
  }

  async health(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  }

  // Session Methods
  async getSessions(params?: ListParams): Promise<SessionListResponse> {
    const response = await this.client.get('/api/v1/sessions', { params });
    return response.data;
  }

  async getSession(sessionId: string): Promise<Session> {
    const response = await this.client.get(`/api/v1/sessions/${sessionId}`);
    return response.data;
  }

  async getStats(): Promise<StatsResponse> {
    const response = await this.client.get('/api/v1/sessions/stats');
    return response.data;
  }

  // Collector Methods
  async scanFolder(folderPath?: string): Promise<ScanResponse> {
    const params = folderPath ? { folder_path: folderPath } : {};
    const response = await this.client.post('/api/v1/collector/scan', params);
    return response.data;
  }

  async importSession(filePath: string): Promise<ImportResponse> {
    const response = await this.client.post('/api/v1/collector/import', { file_path: filePath });
    return response.data;
  }

  async importAll(folderPath?: string): Promise<ImportAllResponse> {
    const params = folderPath ? { folder_path: folderPath } : {};
    const response = await this.client.post('/api/v1/collector/import_all', params);
    return response.data;
  }

  // Curator Methods
  async evaluateSession(sessionId: string): Promise<EvaluateResponse> {
    const response = await this.client.post(`/api/v1/curator/evaluate/${sessionId}`);
    return response.data;
  }

  async evaluateAll(): Promise<EvaluateAllResponse> {
    const response = await this.client.post('/api/v1/curator/evaluate_all');
    return response.data;
  }

  async getCuratorStatus(): Promise<any> {
    const response = await this.client.get('/api/v1/curator/status');
    return response.data;
  }

  // Reviewer Methods
  async getPendingReviews(page: number = 1, pageSize: number = 20): Promise<PendingResponse> {
    const response = await this.client.get('/api/v1/reviewer/pending', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }

  async approveSession(sessionId: string, notes?: string, score?: number): Promise<ReviewResponse> {
    const response = await this.client.post(`/api/v1/reviewer/approve/${sessionId}`, {
      notes,
      score
    });
    return response.data;
  }

  async rejectSession(sessionId: string, notes?: string, score?: number): Promise<ReviewResponse> {
    const response = await this.client.post(`/api/v1/reviewer/reject/${sessionId}`, {
      notes,
      score
    });
    return response.data;
  }

  async batchApprove(sessionIds: string[]): Promise<BatchReviewResponse> {
    const response = await this.client.post('/api/v1/reviewer/batch/approve', {
      session_ids: sessionIds
    });
    return response.data;
  }

  async batchReject(sessionIds: string[]): Promise<BatchReviewResponse> {
    const response = await this.client.post('/api/v1/reviewer/batch/reject', {
      session_ids: sessionIds
    });
    return response.data;
  }
}
