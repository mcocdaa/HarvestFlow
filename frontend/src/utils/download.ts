export const saveBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

export const basename = (filePath: string) => filePath.split(/[\\/]/).pop() || '';

export const filenameFromDisposition = (disposition?: string | null, fallback = 'download') => {
  const match = disposition?.match(/filename="?([^";]+)"?/);
  return match?.[1] ?? fallback;
};
