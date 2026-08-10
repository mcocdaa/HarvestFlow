import { useEffect, useCallback } from 'react';

export const useKeyboardShortcut = (
  key: string,
  handler: (e: KeyboardEvent) => void,
  metaKey = false
) => {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target?.tagName) return;
      const tagName = target.tagName.toLowerCase();
      if (tagName === 'input' || tagName === 'textarea' || tagName === 'button' || target.isContentEditable || target.contentEditable === 'true') {
        return;
      }

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
