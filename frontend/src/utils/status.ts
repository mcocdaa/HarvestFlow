export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    approved: 'var(--flow-status-approved)',
    curated: 'var(--flow-status-curated)',
    rejected: 'var(--flow-status-rejected)',
    raw: 'var(--flow-status-raw)',
  };
  return colors[status] || 'var(--flow-status-raw)';
};
