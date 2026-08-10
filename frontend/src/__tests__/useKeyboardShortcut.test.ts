import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut';

function createTargetDiv(): HTMLDivElement {
  const target = document.createElement('div');
  target.setAttribute('data-testid', 'shortcut-target');
  document.body.appendChild(target);
  return target;
}

function dispatchKeyDown(target: HTMLElement, options: KeyboardEventInit) {
  const event = new KeyboardEvent('keydown', {
    ...options,
    bubbles: true,
  });
  target.dispatchEvent(event);
}

describe('useKeyboardShortcut', () => {
  afterEach(() => {
    // Clean up any stray elements
    document.body.innerHTML = '';
  });

  it('should call handler when key matches with metaKey', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Enter', handler, true));
    const target = createTargetDiv();

    act(() => {
      dispatchKeyDown(target, { key: 'Enter', metaKey: true });
    });

    expect(handler).toHaveBeenCalled();
  });

  it('should call handler with ctrlKey as metaKey alternative', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Enter', handler, true));
    const target = createTargetDiv();

    act(() => {
      dispatchKeyDown(target, { key: 'Enter', ctrlKey: true });
    });

    expect(handler).toHaveBeenCalled();
  });

  it('should not call handler when target is an input element', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Enter', handler, true));

    const input = document.createElement('input');
    document.body.appendChild(input);

    act(() => {
      dispatchKeyDown(input, { key: 'Enter', metaKey: true });
    });

    expect(handler).not.toHaveBeenCalled();
  });

  it('should not call handler when target is a textarea element', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Enter', handler, true));

    const textarea = document.createElement('textarea');
    document.body.appendChild(textarea);

    act(() => {
      dispatchKeyDown(textarea, { key: 'Enter', metaKey: true });
    });

    expect(handler).not.toHaveBeenCalled();
  });

  it('should not call handler when target is a button element', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Enter', handler, true));

    const button = document.createElement('button');
    document.body.appendChild(button);

    act(() => {
      dispatchKeyDown(button, { key: 'Enter', metaKey: true });
    });

    expect(handler).not.toHaveBeenCalled();
  });

  it('should not call handler when target is contentEditable', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Enter', handler, true));

    const div = document.createElement('div');
    div.contentEditable = 'true';
    document.body.appendChild(div);

    act(() => {
      dispatchKeyDown(div, { key: 'Enter', metaKey: true });
    });

    expect(handler).not.toHaveBeenCalled();
  });

  it('should not call handler when key does not match', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Enter', handler, true));
    const target = createTargetDiv();

    act(() => {
      dispatchKeyDown(target, { key: 'Escape', metaKey: true });
    });

    expect(handler).not.toHaveBeenCalled();
  });

  it('should call handler on regular div (not input/textarea/contentEditable)', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut('Backspace', handler, true));
    const target = createTargetDiv();

    act(() => {
      dispatchKeyDown(target, { key: 'Backspace', metaKey: true });
    });

    expect(handler).toHaveBeenCalled();
  });
});
