import { useEffect, useCallback } from 'react';

export const useKeyboardShortcut = (
  key: string,
  handler: (e: KeyboardEvent) => void,
  metaKey = false
) => {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const matchesKey = e.key === key;
      const matchesMeta = !metaKey || (e.metaKey || e.ctrlKey);

      if (matchesKey && matchesMeta) {
        e.preventDefault();
        handler(e);
      }
    },
    [key, handler, metaKey]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
};
