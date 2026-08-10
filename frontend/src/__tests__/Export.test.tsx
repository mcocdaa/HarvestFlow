import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Export from '../pages/Export';

vi.mock('../services', () => ({
  exporterApi: {
    getHistory: vi.fn(),
    getFormats: vi.fn(),
    exportSessions: vi.fn(),
  },
}));

import { exporterApi } from '../services';

describe('Export Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const setupMocks = () => {
    (exporterApi.getHistory as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { exports: [] },
    });
    (exporterApi.getFormats as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { formats: ['sharegpt', 'alpaca'] },
    });
  };

  it('should render version as a text input, not a number input', async () => {
    setupMocks();
    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('Export Settings')).toBeInTheDocument();
    });

    // The version field should be a regular <input type="text"> not a number input
    // In antd 5, Form.Item name="version" generates id="version" on the input
    const versionInput = document.getElementById('version') as HTMLInputElement;
    expect(versionInput).toBeTruthy();
    // InputNumber renders with role="spinbutton", regular Input does not
    expect(versionInput.getAttribute('role')).not.toBe('spinbutton');
  });

  it('should render task_type select field', async () => {
    setupMocks();
    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('Task Type (optional)')).toBeInTheDocument();
    });
  });

  it('should render tags select field with tags mode', async () => {
    setupMocks();
    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('Tags (optional)')).toBeInTheDocument();
    });
  });
});
